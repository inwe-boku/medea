# %% imports
from datetime import datetime

import numpy as np
import pandas as pd

import config as cfg
from src.utils.data_processing import download_file, medea_path, download_energy_balance, process_energy_balance

idx = pd.IndexSlice

eta_hydro_storage = 0.9
# ======================================================================================================================
# %% download and process opsd time series

url_opsd = 'https://data.open-power-system-data.org/time_series/latest/time_series_60min_singleindex.csv'
opsd_file = medea_path('data', 'raw', 'opsd_time_series_60min.csv')
download_file(url_opsd, opsd_file)
ts_opsd = pd.read_csv(opsd_file)

# create medea time series dataframe
ts_medea = ts_opsd[
    ['utc_timestamp', 'cet_cest_timestamp', 'AT_load_actual_entsoe_transparency', 'AT_solar_generation_actual',
     'AT_wind_onshore_generation_actual', 'DE_load_actual_entsoe_transparency',
     'DE_solar_generation_actual', 'DE_solar_capacity', 'DE_wind_onshore_generation_actual', 'DE_wind_onshore_capacity',
     'DE_wind_offshore_generation_actual', 'DE_wind_offshore_capacity', 'DE_price_day_ahead']]
del ts_opsd

ts_medea = ts_medea.copy()
ts_medea.set_index(pd.DatetimeIndex(ts_medea['utc_timestamp']), inplace=True)
ts_medea.drop('utc_timestamp', axis=1, inplace=True)
ts_medea.rename(columns={'AT_load_actual_entsoe_transparency': 'AT-power-load',
                         'AT_solar_generation_actual': 'AT-pv-generation',
                         'AT_wind_onshore_generation_actual': 'AT-wind_on-generation',
                         'DE_load_actual_entsoe_transparency': 'DE-power-load',
                         'DE_solar_generation_actual': 'DE-pv-generation',
                         'DE_solar_capacity': 'DE-pv-capacity',
                         'DE_wind_onshore_generation_actual': 'DE-wind_on-generation',
                         'DE_wind_onshore_capacity': 'DE-wind_on-capacity',
                         'DE_wind_offshore_generation_actual': 'DE-wind_off-generation',
                         'DE_wind_offshore_capacity': 'DE-wind_off-capacity',
                         'DE_price_day_ahead': 'price_day_ahead'}, inplace=True)
if ts_medea.index.max() < pd.Timestamp(f'{ts_medea.index.max().year}-07-01 00:00:00', tz='UTC'):
    df_expand = pd.DataFrame(
        index=pd.date_range(start=ts_medea.index.max() + pd.Timedelta(hours=1),
                            end=pd.Timestamp(f'{ts_medea.index.max().year}-07-01 00:00:00', tz='UTC'), freq='H'),
        columns=ts_medea.columns)
    ts_medea = ts_medea.append(df_expand)

ts_medea['AT-wind_off-generation'] = np.nan

# %% append ENTSO-E data on hydro generation
ts_hydro_generation = pd.read_csv(medea_path('data', 'processed', 'generation_hydro.csv'), index_col=[0])
ts_hydro_generation.index = pd.DatetimeIndex(ts_hydro_generation.index).tz_localize('utc')

ts_medea['AT-ror-generation'] = ts_hydro_generation['ror_AT']
ts_medea['DE-ror-generation'] = ts_hydro_generation['ror_DE']
ts_medea['DE-hydro-generation'] = ts_hydro_generation[['ror_DE', 'res_DE']].sum(axis=1) + \
                                  0.186 * ts_hydro_generation['psp_gen_DE']
# German pumped storages with natural inflows (18.6 % of installed PSP capacity, according to
# https://www.fwt.fichtner.de/userfiles/fileadmin-fwt/Publikationen/WaWi_2017_10_Heimerl_Kohler_PSKW.pdf) are included
# in official hydropower generation numbers.

# %% scale intermittent generation to match annual numbers from national energy balances
cols = ['pv', 'wind_on', 'wind_off', 'ror', 'load']
first_year = max(ts_medea.index.year.min(), 2010)
last_year = ts_medea.index.year.max()
scale_index = pd.MultiIndex.from_product([cols, [str(yr) for yr in range(first_year, last_year)]])
scaling_factor = pd.DataFrame(data=1, columns=cfg.zones, index=scale_index)
# download energy balances
download_energy_balance('AT')
url_econtrol = 'https://www.e-control.at/documents/1785851/1811609/BStGes-JR1_Bilanz.xlsx'
download_file(url_econtrol, medea_path('data', 'raw', 'BStGes-JR1_Bilanz.xlsx'))

# ---------
# Austria - PV, wind, run-of-river
# read energy balance for Austria
nbal_at_cons = pd.read_excel(medea_path('data', 'raw', 'enbal_AT.xlsx'), sheet_name='Elektrische Energie',
                             header=[196], index_col=[0], nrows=190,
                             na_values=['-']).astype('float').dropna(axis=0, how='all')
nbal_at_pv = pd.read_excel(medea_path('data', 'raw', 'enbal_AT.xlsx'), sheet_name='Photovoltaik',
                           header=[196], index_col=[0], nrows=1, na_values=['-']).astype('float').dropna(axis=1)
nbal_at_wind = pd.read_excel(medea_path('data', 'raw', 'enbal_AT.xlsx'), sheet_name='Wind',
                             header=[196], index_col=[0], nrows=1, na_values=['-']).astype('float').dropna(axis=1)
eca_at_hydro = pd.read_excel(medea_path('data', 'raw', 'BStGes-JR1_Bilanz.xlsx'), sheet_name='Erz',
                             header=[8], index_col=[0], nrows=37)
eca_at_hydro.drop('Einheit', inplace=True)
eca_at_hydro.replace(to_replace='-', value=np.nan, inplace=True)
nbal_at_hydro = nbal_at_cons.loc['aus Wasserkraft', :].sum()

for year in range(first_year, last_year):
    if ts_medea.loc[str(year), 'AT-pv-generation'].sum() > 0:
        scaling_factor.loc[idx['pv', str(year)], 'AT'] = nbal_at_pv.loc[:, year].values / \
                                                         ts_medea.loc[str(year), 'AT-pv-generation'].sum()
    if ts_medea.loc[str(year), 'AT-wind_on-generation'].sum() > 0:
        scaling_factor.loc[idx['wind_on', str(year)], 'AT'] = nbal_at_wind.loc[:, year].values / \
                                                              ts_medea.loc[str(year), 'AT-wind_on-generation'].sum()
    if ts_medea.loc[str(year), 'AT-ror-generation'].sum() > 0:
        scaling_factor.loc[idx['ror', str(year)], 'AT'] = eca_at_hydro.loc[year, 'Laufkraft-\nwerke'] * \
                                                          (nbal_at_hydro[year] / 1000) / \
                                                          eca_at_hydro.loc[year, 'Summe\nWasser-\nkraft'] / \
                                                          (ts_medea.loc[str(year), 'AT-ror-generation'].sum() / 1000)
    if ts_medea.loc[str(year), 'AT-power-load'].sum() > 0:
        scaling_factor.loc[idx['load', str(year)], 'AT'] = \
            nbal_at_cons.loc[['Energetischer Endverbrauch', 'Transportverluste'], year].sum() / \
            ts_medea.loc[str(year), 'AT-power-load'].sum()

# ---------
# Germany - PV, wind
url = 'https://www.erneuerbare-energien.de/EE/Redaktion/DE/Downloads/' \
      'zeitreihen-zur-entwicklung-der-erneuerbaren-energien-in-deutschland-1990-2019-excel-en.xlsx' \
      '?__blob=publicationFile'
download_file(url, medea_path('data', 'raw', 'res_DE.xlsx'))
res_de = pd.read_excel(medea_path('data', 'raw', 'res_DE.xlsx'), sheet_name='3', header=[7], index_col=[0], nrows=13)

download_energy_balance('DE')
process_energy_balance('DE')
nbal_de_el = pd.read_csv(medea_path('data', 'processed', 'enbal_DE_el.csv'), index_col=[0], sep=';')

for year in range(first_year, last_year):
    # wind_off_gen_nbal = nbal_de.loc['Wind energy offshore', str(cfg.year)] * 10**3
    if ts_medea.loc[str(year), 'DE-pv-generation'].sum() > 0:
        scaling_factor.loc[idx['pv', str(year)], 'DE'] = \
            res_de.loc['Solar Photovoltaic', str(year)].values * 10 ** 3 / \
            ts_medea.loc[str(year), 'DE-pv-generation'].sum()

    if ts_medea.loc[str(year), 'DE-wind_on-generation'].sum() > 0:
        scaling_factor.loc[idx['wind_on', str(year)], 'DE'] = \
            res_de.loc['Wind energy onshore', str(year)].values * 10 ** 3 / \
            ts_medea.loc[str(year), 'DE-wind_on-generation'].sum()

    if ts_medea.loc[str(year), 'DE-wind_off-generation'].sum() > 0:
        scaling_factor.loc[idx['wind_off', str(year)], 'DE'] = \
            res_de.loc['Wind energy offshore', str(year)].values * 10 ** 3 / \
            ts_medea.loc[str(year), 'DE-wind_off-generation'].sum()

    if ts_medea.loc[str(year), 'DE-hydro-generation'].sum() > 0:
        scaling_factor.loc[idx['ror', str(year)], 'DE'] = \
            res_de.loc['Hydropower ¹⁾', str(year)].values * 10 ** 3 / \
            ts_medea.loc[str(year), 'DE-hydro-generation'].sum()

    if ts_medea.loc[str(year), 'DE-power-load'].sum() > 0:
        scaling_factor.loc[idx['load', str(year)], 'DE'] = \
            nbal_de_el.loc[['ENDENERGIEVERBRAUCH', 'Fackel- u. Leitungsverluste'], str(year)].sum() * 10 ** 3 / \
            ts_medea.loc[str(year), 'DE-power-load'].sum()

# ----------------------------------------------------------------------------------------------------------------------
# %% intermittent capacities
itm_capacities = pd.read_excel(medea_path('data', 'processed', 'data_static.xlsx'), 'INITIAL_CAP_R',
                               header=[0], index_col=[0, 1])
itm_capacities['date'] = pd.to_datetime(itm_capacities.index.get_level_values(1) + 1, format='%Y',
                                        utc='true') - pd.Timedelta(days=184)
itm_capacities = itm_capacities.unstack(level=0)
itm_capacities.set_index(('date', 'AT'), inplace=True)
ts_medea['AT-pv-capacity'] = itm_capacities[('pv', 'AT')]
ts_medea['AT-pv-capacity'] = ts_medea['AT-pv-capacity'].interpolate()
ts_medea['AT-wind_on-capacity'] = itm_capacities[('wind_on', 'AT')]
ts_medea['AT-wind_on-capacity'] = ts_medea['AT-wind_on-capacity'].interpolate()
ts_medea['AT-wind_off-capacity'] = np.nan
for reg in cfg.zones:
    ts_medea[f'{reg}-ror-capacity'] = itm_capacities[('ror', reg)]
    ts_medea[f'{reg}-ror-capacity'] = ts_medea[f'{reg}-ror-capacity'].interpolate()

# %% convert capacities from MW to GW
ts_medea['DE-pv-capacity'] = ts_medea['DE-pv-capacity'] / 1000
ts_medea['DE-wind_on-capacity'] = ts_medea['DE-wind_on-capacity'] / 1000
ts_medea['DE-wind_off-capacity'] = ts_medea['DE-wind_off-capacity'] / 1000

# ----------------------------------------------------------------------------------------------------------------------
# %% generate scaled generation profiles
intermittents = ['pv', 'wind_on', 'wind_off', 'ror']
for reg in cfg.zones:
    for itm in intermittents:
        ts_medea[f'{reg}-{itm}-profile'] = 0
        # convert generation from MW to GW
        ts_medea[f'{reg}-{itm}-generation'] = ts_medea[f'{reg}-{itm}-generation'] / 1000
        for yr in range(first_year, last_year):
            if scaling_factor.loc[idx[itm, str(yr)], reg] < 2:
                ts_medea.loc[str(yr), f'{reg}-{itm}-profile'] = \
                    ts_medea.loc[str(yr), f'{reg}-{itm}-generation'] / \
                    ts_medea.loc[str(yr), f'{reg}-{itm}-capacity'] * \
                    scaling_factor.loc[idx[itm, str(yr)], reg]
            else:
                ts_medea.loc[str(yr), f'{reg}-{itm}-profile'] = ts_medea.loc[str(yr), f'{reg}-{itm}-generation'] / \
                                                                ts_medea.loc[str(yr), f'{reg}-{itm}-capacity']
        # cut off profile peaks larger than 1
        ts_medea.loc[ts_medea[f'{reg}-{itm}-profile'] > 1] = 1

# ----------------------------------------------------------------------------------------------------------------------
# %% scale electricity load
for reg in cfg.zones:
    for yr in range(first_year, last_year):
        if scaling_factor.loc[idx['load', str(yr)], reg] < 2:
            ts_medea.loc[str(yr), f'{reg}-power-load'] = \
                ts_medea.loc[str(yr), f'{reg}-power-load'] * \
                scaling_factor.loc[idx['load', str(yr)], reg]

# ----------------------------------------------------------------------------------------------------------------------
# %% convert load from MW to GW
ts_medea['AT-power-load'] = ts_medea['AT-power-load'] / 1000
ts_medea['DE-power-load'] = ts_medea['DE-power-load'] / 1000

# ----------------------------------------------------------------------------------------------------------------------
# %% heat consumption data
ts_load_ht = pd.read_csv(medea_path('data', 'processed', 'heat_hourly_consumption.csv'),
                         index_col=[0], header=[0, 1])
ts_load_ht.index = pd.DatetimeIndex(ts_load_ht.index).tz_localize('utc')
for reg in cfg.zones:
    ts_medea[f'{reg}-heat-load'] = ts_load_ht.loc[:, reg].sum(axis=1)

# ----------------------------------------------------------------------------------------------------------------------
# %% commercial flows
ts_flows = pd.read_csv(medea_path('data', 'processed', 'commercial_flows.csv'), index_col=[0])
ts_flows.index = pd.DatetimeIndex(ts_flows.index).tz_localize('utc')
for reg in cfg.zones:
    ts_medea[f'{reg}-imports-flow'] = ts_flows.loc[:, f'imp_{reg}'] / 1000
    ts_medea[f'{reg}-exports-flow'] = ts_flows.loc[:, f'exp_{reg}'] / 1000

# ----------------------------------------------------------------------------------------------------------------------
# %% scaling of hydro reservoir inflows
# 1) how much is reservoir generation according to energy balance? -- infer from ECA data and scale to energy balance
entsoe_ror = ts_medea.loc[:, 'AT-ror-generation'].resample('Y').sum()
entsoe_ror.index = entsoe_ror.index.year
factor_ror = scaling_factor.loc[idx['ror', :], 'AT']
factor_ror.index = factor_ror.index.get_level_values(1).astype('int')
nbal_at_ror = factor_ror * entsoe_ror
nbal_at_ror.loc[nbal_at_ror < 10000] = np.nan
nbal_at_rsvr = nbal_at_hydro / 1000 - nbal_at_ror

# 2) scaling factor for hydro storage generation and inflows
scaling_factor_nflw = nbal_at_rsvr / eca_at_hydro.loc[:, 'Speicher-\nkraftwerke']

# 3) ECA inflows to hydro reservoirs
eca_at_rsvr = pd.read_excel(medea_path('data', 'raw', 'BStGes-JR1_Bilanz.xlsx'), sheet_name='Bil', header=[7],
                            index_col=[0], nrows=37)
eca_at_rsvr.drop('Einheit', inplace=True)
eca_at_rsvr.replace(to_replace='- ', value=np.nan, inplace=True)
eca_at_nflw = eca_at_hydro.loc[:, 'Speicher-\nkraftwerke'] / eta_hydro_storage - \
              eca_at_rsvr.loc[:, 'Verbrauch\nfür Pump-\nspeicher'] * eta_hydro_storage

# 4) inflows in line with energy balance
nbal_at_nflw = eca_at_nflw * scaling_factor_nflw

# %% filling rates of hydro reservoirs
df_hydro_fill = pd.read_csv(medea_path('data', 'processed', 'reservoir_filling.csv'), index_col=[0])
df_hydro_fill.index = pd.DatetimeIndex(df_hydro_fill.index).tz_localize('utc')
ts_hydro_fill = pd.DataFrame(
    index=pd.date_range(datetime(df_hydro_fill.head(1).index.year[0], 1, 1, 0, 0),
                        datetime(df_hydro_fill.tail(1).index.year[0], 12, 31, 23, 0),
                        freq='h', tz='utc'), columns=cfg.zones)
ts_hydro_fill.update(df_hydro_fill[cfg.zones].resample('H').interpolate(method='pchip'))
ts_hydro_fill = ts_hydro_fill.fillna(method='pad')
ts_hydro_fill = ts_hydro_fill.fillna(method='bfill')
for reg in cfg.zones:
    ts_medea[f'{reg}-fill-reservoir'] = ts_hydro_fill.loc[:, reg] / df_hydro_fill[reg].max()

# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
# %% reservoir inflows
inflows = pd.DataFrame(columns=cfg.zones)
for reg in cfg.zones:
    # upsample turbining and pumping to fill rate times and calculate balance at time of fill readings
    inflows[reg] = (df_hydro_fill[reg] - df_hydro_fill[reg].shift(periods=-1) - ts_hydro_generation[
        f'psp_con_{reg}'].resample(
        'W-MON').sum() + ts_hydro_generation[f'psp_gen_{reg}'].resample('W-MON').sum() + ts_hydro_generation[
                        f'res_{reg}'].resample(
        'W-MON').sum()) / 1000 / 168
    # shift inflow estimate up to avoid negative inflows
    if inflows[reg].min() < 0:
        inflows[reg] = inflows[reg] - inflows[reg].min() * 1.1

inflows_hr = inflows.resample('H').interpolate(method='pchip')

for yr in nbal_at_nflw.dropna().index:
    inflows_hr.loc[str(yr), 'AT'] = inflows_hr.loc[str(yr), 'AT'] * nbal_at_nflw.loc[yr] / inflows_hr.loc[
        str(yr), 'AT'].sum()

for reg in cfg.zones:
    ts_medea[f'{reg}-inflows-reservoir'] = inflows_hr[reg]
    ts_medea.loc[ts_medea[f'{reg}-inflows-reservoir'] < 0, f'{reg}-inflows-reservoir'] = 0

# ----------------------------------------------------------------------------------------------------------------------
# %% fuel and co2 price data
df_fuels = pd.read_csv(medea_path('data', 'processed', 'monthly_fuel_prices.csv'), index_col=[0], parse_dates=True)
ts_prices = df_fuels[['NGas_DE', 'Brent_UK', 'Coal_SA']]
ts_prices = ts_prices.resample('H').interpolate('pchip')
ts_prices.rename({'NGas_DE': 'Gas', 'Coal_SA': 'Coal', 'Brent_UK': 'Oil'}, axis=1, inplace=True)
ts_prices.index = ts_prices.index.tz_localize('utc')
df_eua = pd.read_csv(medea_path('data', 'processed', 'co2_price.csv'),
                     index_col=[0], parse_dates=True)
df_eua.index = df_eua.index.tz_localize('utc')
ts_prices['EUA'] = df_eua.resample('H').interpolate('pchip')
ts_medea = pd.merge(ts_medea, ts_prices, how='outer', left_index=True, right_index=True)

# ----------------------------------------------------------------------------------------------------------------------
# %% Write only one date, call that column DateTime
ts_medea.index.name = 'DateTime'
ts_medea.drop(['cet_cest_timestamp'], axis=1, inplace=True)
ts_medea.to_csv(medea_path('data', 'processed', 'medea_regional_timeseries.csv'))
