import os
import sys

import numpy as np
import pandas as pd

import config as cfg
from src.tools.data_processing import heat_yr2day, heat_day2hr, resample_index, download_file

# ----------------------------------------------------------------------------
# set current working directory
# ----------------------------------------------------------------------------
# if current working directory does not include the "data'-folder, use os.chdir() below to set working directory
os.chdir(os.path.join(cfg.MEDEA_ROOT_DIR))  # <<<--- if necessary, set path
dir_path = os.getcwd()
if os.path.isdir(os.path.join(dir_path, 'data', 'raw')) is False:
    print('Please use \'os.chdir()\' to set current working directory such that it includes the \'data\'-folder.')
    sys.exit(1)

# ----------------------------------------------------------------------------
# download data from sources
# ----------------------------------------------------------------------------
# Austrian energy balance as provided by Statistik Austria
url = 'http://www.statistik.at/wcm/idc/idcplg?IdcService=GET_NATIVE_FILE&RevisionSelectionMethod=LatestReleased&dDocName=029955'
enbal_at = os.path.join(cfg.MEDEA_ROOT_DIR, 'data', 'raw', 'enbal_AT.xlsx')
download_file(url, enbal_at)
ht_enduse_at = pd.read_excel(enbal_at, sheet_name='Fernwärme', header=[438], index_col=[0], nrows=24,
                             na_values=['-']).astype('float')

# German energy balance as provided by AGEB
ht_enduse_de = pd.DataFrame()
url_extensions = {12: 'xlsx', 13: 'xls', 14: 'xls', 15: 'xlsx', 16: 'xls', 17: 'xlsx'}
for yr in range(12, 18):
    url = f'https://ag-energiebilanzen.de/index.php?article_id=29&fileName=bilanz{yr}d.{url_extensions[yr]}'
    enbal_de = os.path.join(cfg.MEDEA_ROOT_DIR, 'data', 'raw', f'enbal_DE_20{yr}.xlsx')
    download_file(url, enbal_de)
    df = pd.read_excel(enbal_de, sheet_name='tj', index_col=[0], usecols=[0, 31], skiprows=list(range(0, 50)),
                       nrows=24, na_values=['-'])
    df.columns = [2000 + yr]
    ht_enduse_de = pd.concat([ht_enduse_de, df], axis=1)

ht_cols = pd.MultiIndex.from_product([cfg.zones, ['HE08', 'HM08', 'HG08', 'WW', 'IND']])
ht_cons = pd.DataFrame(index=range(2012, 2018), columns=ht_cols)

# Assumptions for further calculations
# * share of heating energy used for hot water preparation: 25%
#   (cf. https://www.umweltbundesamt.at/fileadmin/site/publikationen/REP0074.pdf, p. 98)
# * share of heat delivered to single-family homes:
#   - in Austria 2/3 of houses are single-family houses, which are home to 40% of the population
#   - in Germany, 65.1% of houses are EFH, 17.2% are ZFH and 17.7% are MFH
#     (cf. https://www.statistik.rlp.de/fileadmin/dokumente/gemeinschaftsveroeff/zen/Zensus_GWZ_2014.pdf)
#   - average space in single-family houses: 127.3 m^2; in multiple dwellings: 70.6 m^2
#   - specific heat consumption: EFH: 147.9 kWh/m^2; MFH: 126.5 kWh/m^2
#     (cf. http://www.rwi-essen.de/media/content/pages/publikationen/rwi-projektberichte/PB_Datenauswertung-Energieverbrauch-privHH.pdf, p. 5)
#   - implied share of heat consumption, assuming on average 7 appartments per MFH: 37.6% EFH; 62.4% MFH

ht_cons.loc[range(2012, 2018), ('AT', 'HE08')] = ht_enduse_at.loc[
                                                     'Private Haushalte', range(2012, 2018)] / 1000 * 0.376 * 0.75
ht_cons.loc[range(2012, 2018), ('AT', 'HM08')] = ht_enduse_at.loc[
                                                     'Private Haushalte', range(2012, 2018)] / 1000 * 0.624 * 0.75
ht_cons.loc[range(2012, 2018), ('AT', 'WW')] = ht_enduse_at.loc[
                                                   'Private Haushalte', range(2012, 2018)] / 1000 * 0.25
ht_cons.loc[range(2012, 2018), ('AT', 'HG08')] = ht_enduse_at.loc[
                                                     'Öffentliche und Private Dienstleistungen', range(2012,
                                                                                                       2018)] / 1000
ht_cons.loc[range(2012, 2018), ('AT', 'IND')] = ht_enduse_at.loc[
                                                    'Produzierender Bereich', range(2012, 2018)] / 1000

ht_cons.loc[range(2012, 2018), ('DE', 'HE08')] = ht_enduse_de.loc['Haushalte', range(2012, 2018)] / 3.6 * 0.376 * 0.75
ht_cons.loc[range(2012, 2018), ('DE', 'HM08')] = ht_enduse_de.loc['Haushalte', range(2012, 2018)] / 3.6 * 0.624 * 0.75
ht_cons.loc[range(2012, 2018), ('DE', 'WW')] = ht_enduse_de.loc['Haushalte', range(2012, 2018)] / 3.6 * 0.25
ht_cons.loc[range(2012, 2018), ('DE', 'HG08')] = ht_enduse_de.loc[
                                                     'Gewerbe, Handel, Dienstleistungen u.übrige Verbraucher', range(
                                                         2012, 2018)] / 3.6
ht_cons.loc[range(2012, 2018), ('DE', 'IND')] = ht_enduse_de.loc[
                                                    'Bergbau, Gew. Steine u. Erden, Verarbeit. Gewerbe insg.', range(
                                                        2012, 2018)] / 3.6

# Accounting for own consumption and line losses
cons_annual = ht_cons * 1.125

# ----------------------------------------------------------------------------
# read data
# ----------------------------------------------------------------------------

df_heat = pd.read_excel(os.path.join(dir_path, 'data', 'raw', 'temp_mean.xlsx'), index_col=[0])
df_heat['year'] = df_heat.index.year
df_heat['weekday'] = df_heat.index.strftime('%a')
# fill NA to prevent NAs in temperature smoothing below
df_heat.fillna(method='pad', inplace=True)

dayrange = pd.date_range(pd.datetime(np.min(df_heat['year']), 1, 1), pd.datetime(np.max(df_heat['year']), 12, 31),
                         freq='D')

cons_pattern = pd.read_excel(os.path.join(dir_path, 'data', 'raw', 'consumption_pattern.xlsx'), 'consumption_pattern',
                             index_col=[0, 1])
cons_pattern = cons_pattern.rename_axis('hour', axis=1)
cons_pattern = cons_pattern.unstack('consumer').stack('hour')

# ----------------------------------------------------------------------------
# calculate heat consumption for each region
# ----------------------------------------------------------------------------
idx = pd.IndexSlice
regions = cfg.zones
ht_consumption = pd.DataFrame(index=resample_index(df_heat.index, 'h'), columns=cons_annual.columns)
for reg in regions:
    cons_daily = heat_yr2day(df_heat[reg], cons_annual.loc[:, reg])
    cons_hourly = heat_day2hr(df_heat[reg], cons_daily, cons_pattern)
    cons_hourly.columns = pd.MultiIndex.from_product([[reg], cons_hourly.columns])
    ht_consumption.loc[:, idx[reg, :]] = cons_hourly

# fill WW and IND
for yr in range(2012, 2018):
    for zn in cfg.zones:
        hrs = len(ht_consumption.loc[str(yr), :])
        ht_consumption.loc[str(yr), idx[zn, 'WW']] = cons_annual.loc[yr, idx[zn, 'WW']] / hrs
        ht_consumption.loc[str(yr), idx[zn, 'IND']] = cons_annual.loc[yr, idx[zn, 'IND']] / hrs

ht_consumption.to_csv(os.path.join(cfg.MEDEA_ROOT_DIR, 'data', 'processed', 'heat_hourly_consumption.csv'))
