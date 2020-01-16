import logging
import os

import numpy as np
import pandas as pd

import config as cfg
from logging_config import setup_logging
from src.tools.data_processing import heat_yr2day, heat_day2hr, resample_index, download_file

YEARS = range(2012, 2018)

setup_logging()

# ----------------------------------------------------------------------------
# download data from sources
# ----------------------------------------------------------------------------
# Austrian energy balance as provided by Statistik Austria
url = 'http://www.statistik.at/wcm/idc/idcplg?IdcService=GET_NATIVE_FILE&RevisionSelectionMethod=LatestReleased&dDocName=029955'
enbal_at = os.path.join(cfg.MEDEA_ROOT_DIR, 'data', 'raw', 'enbal_AT.xlsx')
logging.info(f'downloading Austrian energy balance')
download_file(url, enbal_at)
ht_enduse_at = pd.read_excel(enbal_at, sheet_name='Fernwärme', header=[438], index_col=[0], nrows=24,
                             na_values=['-']).astype('float')

# German energy balance as provided by AGEB
ht_enduse_de = pd.DataFrame()
url_extensions = {12: 'xlsx', 13: 'xls', 14: 'xls', 15: 'xlsx', 16: 'xls', 17: 'xlsx'}
for yr in [x - 2000 for x in YEARS]:
    url = f'https://ag-energiebilanzen.de/index.php?article_id=29&fileName=bilanz{yr}d.{url_extensions[yr]}'
    enbal_de = os.path.join(cfg.MEDEA_ROOT_DIR, 'data', 'raw', f'enbal_DE_20{yr}.xlsx')
    logging.info(f'downloading Germany energy balance for year 20{yr}')
    download_file(url, enbal_de)
    df = pd.read_excel(enbal_de, sheet_name='tj', index_col=[0], usecols=[0, 31], skiprows=list(range(0, 50)),
                       nrows=24, na_values=['-'])
    df.columns = [2000 + yr]
    ht_enduse_de = pd.concat([ht_enduse_de, df], axis=1)

ht_cols = pd.MultiIndex.from_product([cfg.zones, ['HE08', 'HM08', 'HG08', 'WW', 'IND']])
ht_cons = pd.DataFrame(index=YEARS, columns=ht_cols)

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

ht_cons.loc[YEARS, ('AT', 'HE08')] = ht_enduse_at.loc['Private Haushalte', YEARS] / 1000 * 0.376 * 0.75
ht_cons.loc[YEARS, ('AT', 'HM08')] = ht_enduse_at.loc['Private Haushalte', YEARS] / 1000 * 0.624 * 0.75
ht_cons.loc[YEARS, ('AT', 'WW')] = ht_enduse_at.loc['Private Haushalte', YEARS] / 1000 * 0.25
ht_cons.loc[YEARS, ('AT', 'HG08')] = ht_enduse_at.loc['Öffentliche und Private Dienstleistungen', YEARS] / 1000
ht_cons.loc[YEARS, ('AT', 'IND')] = ht_enduse_at.loc['Produzierender Bereich', YEARS] / 1000

ht_cons.loc[YEARS, ('DE', 'HE08')] = ht_enduse_de.loc['Haushalte', YEARS] / 3.6 * 0.376 * 0.75
ht_cons.loc[YEARS, ('DE', 'HM08')] = ht_enduse_de.loc['Haushalte', YEARS] / 3.6 * 0.624 * 0.75
ht_cons.loc[YEARS, ('DE', 'WW')] = ht_enduse_de.loc['Haushalte', YEARS] / 3.6 * 0.25
ht_cons.loc[YEARS, ('DE', 'HG08')] = ht_enduse_de.loc['Gewerbe, Handel, Dienstleistungen u.übrige Verbraucher',
                                                      YEARS] / 3.6
ht_cons.loc[YEARS, ('DE', 'IND')] = ht_enduse_de.loc['Bergbau, Gew. Steine u. Erden, Verarbeit. Gewerbe insg.',
                                                     YEARS] / 3.6

# Accounting for own consumption and line losses
cons_annual = ht_cons * 1.125

# ----------------------------------------------------------------------------
# read data
# ----------------------------------------------------------------------------

df_heat = pd.read_excel(os.path.join(cfg.MEDEA_ROOT_DIR, 'data', 'processed', 'temp_daily_mean.csv'), index_col=[0])
df_heat['year'] = df_heat.index.year
df_heat['weekday'] = df_heat.index.strftime('%a')
# fill NA to prevent NAs in temperature smoothing below
df_heat.fillna(method='pad', inplace=True)

dayrange = pd.date_range(pd.datetime(np.min(df_heat['year']), 1, 1), pd.datetime(np.max(df_heat['year']), 12, 31),
                         freq='D')

cons_pattern = pd.read_excel(os.path.join(cfg.MEDEA_ROOT_DIR, 'data', 'raw', 'consumption_pattern.xlsx'),
                             'consumption_pattern',
                             index_col=[0, 1])
cons_pattern = cons_pattern.rename_axis('hour', axis=1)
cons_pattern = cons_pattern.unstack('consumer').stack('hour')

# ----------------------------------------------------------------------------
# calculate heat consumption for each region
# ----------------------------------------------------------------------------
idx = pd.IndexSlice
regions = cfg.zones
logging.info('calculating hourly heat demand')
ht_consumption = pd.DataFrame(index=resample_index(df_heat.index, 'h'), columns=cons_annual.columns)
for reg in regions:
    cons_daily = heat_yr2day(df_heat[reg], cons_annual.loc[:, reg])
    cons_hourly = heat_day2hr(df_heat[reg], cons_daily, cons_pattern)
    cons_hourly.columns = pd.MultiIndex.from_product([[reg], cons_hourly.columns])
    ht_consumption.loc[:, idx[reg, :]] = cons_hourly

# fill WW and IND
for yr in YEARS:
    for zn in cfg.zones:
        hrs = len(ht_consumption.loc[str(yr), :])
        ht_consumption.loc[str(yr), idx[zn, 'WW']] = cons_annual.loc[yr, idx[zn, 'WW']] / hrs
        ht_consumption.loc[str(yr), idx[zn, 'IND']] = cons_annual.loc[yr, idx[zn, 'IND']] / hrs

heat_cons_file = os.path.join(cfg.MEDEA_ROOT_DIR, 'data', 'processed', 'heat_hourly_consumption.csv')
ht_consumption.to_csv(heat_cons_file)
logging.info(f'exported hourly heat demand to {heat_cons_file}')
