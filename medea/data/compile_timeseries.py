import os

import pandas as pd

import config as cfg

"""
create single file with all time series input for power system model medea.
take files from helpers data repository, join data and write to model data folder
"""
# TODO: adjust all helper files such that data is written to helper data repository.
# TODO: move input files from model data to helpers data

# read opsd data
ts_opsd = pd.read_csv(os.path.join(cfg.folder, 'data', 'raw', 'time_series_60min_singleindex.csv'))
# create MEDEA time series dataframe
ts_medea = ts_opsd[
    ['utc_timestamp', 'cet_cest_timestamp', 'AT_load_entsoe_transparency', 'AT_solar_generation_actual',
     'AT_wind_onshore_generation_actual', 'DE_load_entsoe_transparency', 'DE_solar_profile',
     'DE_wind_onshore_profile', 'DE_wind_offshore_profile', 'DE_price_day_ahead']]
del ts_opsd
ts_medea = ts_medea.copy()
ts_medea.set_index(pd.DatetimeIndex(ts_medea['utc_timestamp']), inplace=True)
ts_medea.drop('utc_timestamp', axis=1, inplace=True)
ts_medea.rename(columns={'AT_load_entsoe_transparency': 'AT-power-load',
                         'AT_solar_generation_actual': 'AT-pv-generation',
                         'AT_wind_onshore_generation_actual': 'AT-wind_on-generation',
                         'DE_load_entsoe_transparency': 'DE-power-load',
                         'DE_solar_profile': 'DE-pv-profile',
                         'DE_wind_onshore_profile': 'DE-wind_on-profile',
                         'DE_wind_offshore_profile': 'DE-wind_off-profile',
                         'DE_price_day_ahead': 'price_day_ahead'}, inplace=True)
if ts_medea.index.max() < pd.Timestamp(f'{ts_medea.index.max().year}-07-01 00:00:00', tz='UTC'):
    df_expand = pd.DataFrame(
        index=pd.date_range(start=ts_medea.index.max()+pd.Timedelta(hours=1),
                            end=pd.Timestamp(f'{ts_medea.index.max().year}-07-01 00:00:00', tz='UTC'), freq='H'),
        columns=ts_medea.columns)
    ts_medea = ts_medea.append(df_expand)

ts_medea['AT-power-load'] = ts_medea['AT-power-load'] / 1000
ts_medea['DE-power-load'] = ts_medea['DE-power-load'] / 1000
ts_medea['AT-pv-generation'] = ts_medea['AT-pv-generation'] / 1000
ts_medea['AT-wind_on-generation'] = ts_medea['AT-wind_on-generation'] / 1000

# intermittent capacities
itm_capacities = pd.read_excel(os.path.join(cfg.folder, 'data', 'processed', 'plant_props.xlsx'), 'itm_installed',
                               header=[0, 1], index_col=[0])
itm_capacities['year'] = itm_capacities.index
itm_capacities['date'] = pd.to_datetime(itm_capacities['year'] + 1, format='%Y', utc='true') - pd.Timedelta(days=184)
itm_capacities.set_index('date', inplace=True)
ts_medea['AT-pv-capacity'] = itm_capacities[('AT', 'pv')]
ts_medea['AT-pv-capacity'] = ts_medea['AT-pv-capacity'].interpolate()
ts_medea['AT-wind_on-capacity'] = itm_capacities[('AT', 'wind_on')]
ts_medea['AT-wind_on-capacity'] = ts_medea['AT-wind_on-capacity'].interpolate()
ts_medea['AT-wind_on-profile'] = ts_medea['AT-wind_on-generation'] / ts_medea['AT-wind_on-capacity']
ts_medea['AT-wind_off-profile'] = 0
ts_medea['AT-pv-profile'] = ts_medea['AT-pv-generation'] / ts_medea['AT-pv-capacity']

# heat consumption data
ts_load_ht = pd.read_csv(os.path.join(cfg.folder, 'data', 'processed', 'heat_hourly_consumption.csv'),
                         index_col=[0], header=[0, 1])
ts_load_ht.index = pd.DatetimeIndex(ts_load_ht.index).tz_localize('utc')
for reg in cfg.zones:
    ts_medea[f'{reg}-heat-load'] = ts_load_ht.loc[:, reg].sum(axis=1)

# read hydro data
ts_hydro_ror = pd.read_csv(os.path.join(cfg.folder, 'data', 'processed', 'generation_hydro.csv'), index_col=[0])
ts_hydro_ror.index = pd.DatetimeIndex(ts_hydro_ror.index).tz_localize('utc')
for reg in cfg.zones:
    ts_medea[f'{reg}-ror-capacity'] = itm_capacities[(reg, 'ror')]
    ts_medea[f'{reg}-ror-capacity'] = ts_medea[f'{reg}-ror-capacity'].interpolate()
    ts_medea[f'{reg}-ror-profile'] = ts_hydro_ror[f'ror_{reg}'] / 1000 / ts_medea[f'{reg}-ror-capacity']

# commercial flows
ts_flows = pd.read_csv(os.path.join(cfg.folder, 'data', 'processed', 'commercial_flows.csv'), index_col=[0])
ts_flows.index = pd.DatetimeIndex(ts_flows.index).tz_localize('utc')
for reg in cfg.zones:
    ts_medea[f'{reg}-imports-flow'] = ts_flows.loc[:, f'imp_{reg}'] / 1000
    ts_medea[f'{reg}-exports-flow'] = ts_flows.loc[:, f'exp_{reg}'] / 1000

# filling rates of hydro reservoirs
df_hydro_fill = pd.read_csv(os.path.join(cfg.folder, 'data', 'processed', 'FillingRateReservoirs.csv'), index_col=[0])
df_hydro_fill.index = pd.DatetimeIndex(df_hydro_fill.index).tz_localize('utc')
ts_hydro_fill = pd.DataFrame(
    index=pd.date_range(pd.datetime(df_hydro_fill.head(1).index.year[0], 1, 1, 0, 0),
                        pd.datetime(df_hydro_fill.tail(1).index.year[0], 12, 31, 23, 0),
                        freq='h', tz='utc'), columns=cfg.zones)
ts_hydro_fill.update(df_hydro_fill[cfg.zones].resample('H').interpolate(method='pchip'))
# ts_hydro_fill.update(df_hydro_fill[cfg.regions].resample('H').interpolate(method='pchip') / df_hydro_fill[cfg.regions].max())
ts_hydro_fill = ts_hydro_fill.fillna(method='pad')
ts_hydro_fill = ts_hydro_fill.fillna(method='bfill')
for reg in cfg.zones:
    ts_medea[f'{reg}-fill-reservoir'] = ts_hydro_fill.loc[:, reg] / df_hydro_fill[reg].max()

# reservoir inflows
inflows = pd.DataFrame(columns=cfg.zones)
for reg in cfg.zones:
    # upsample turbining and pumping to fill rate times and calculate balance at time of fill readings
    inflows[reg] = (df_hydro_fill[reg] - df_hydro_fill[reg].shift(periods=-1) - ts_hydro_ror[f'psp_con_{reg}'].resample(
        'W-MON').sum() + ts_hydro_ror[f'psp_gen_{reg}'].resample('W-MON').sum() + ts_hydro_ror[f'res_{reg}'].resample(
        'W-MON').sum())/1000 / 168
    inflows.loc[inflows[reg]<0, reg] = 0
    # downsample to hours
    ts_medea[f'{reg}-inflows-reservoir'] = inflows[reg].resample('H').interpolate(method='pchip')
    ts_medea.loc[ts_medea[f'{reg}-inflows-reservoir'] < 0, f'{reg}-inflows-reservoir'] = 0

# fuel price data
df_fuels = pd.read_excel(os.path.join(cfg.folder, 'data', 'raw', 'monthly_fuel_prices.xlsx'), 'fuels_monthly',
                         skiprows=[1, 2])  # , parse_dates=True)
df_fuels.set_index('Date', inplace=True)
ts_prices = df_fuels[['Ngas_Border_MWh', 'Brent_MWh', 'Coal_SA_MWh']]
ts_prices = ts_prices.resample('H').interpolate('pchip')
ts_prices.rename({'Ngas_Border_MWh': 'Gas', 'Coal_SA_MWh': 'Coal', 'Brent_MWh': 'Oil'}, axis=1, inplace=True)
ts_prices.index = ts_prices.index.tz_localize('utc')
df_eua =  pd.read_excel(os.path.join(cfg.folder, 'data', 'raw', 'monthly_fuel_prices.xlsx'), 'EUA_daily')
df_eua.set_index('Date', inplace=True)
df_eua.index = df_eua.index.tz_localize('utc')
ts_prices['EUA'] = df_eua.resample('H').interpolate('pchip')
# ts_prices = pd.read_excel(os.path.join(cfg.folder, 'data', 'raw', 'prices_medea.xlsx'), index_col=[0])
# ts_prices.index = ts_prices.index.tz_localize('utc')
# ts_prices = ts_prices.resample('1H', convention='end').interpolate(method='pchip')  # .pad()
# ts_prices.drop(ts_prices.tail(1).index, inplace=True)
ts_medea = pd.merge(ts_medea, ts_prices, how='outer', left_index=True, right_index=True)

# Write only one date, call that column DateTime
ts_medea.index.name = 'DateTime'
ts_medea.drop(['cet_cest_timestamp'], axis=1, inplace=True)
ts_medea.to_csv(os.path.join(cfg.folder, 'data', 'processed', 'medea_regional_timeseries.csv'))

"""
### need to adjust data

# generate availability time series
ts_outage = pd.read_csv(os.path.join(cfg.folder, 'data', 'outages_integer.csv'))
ts_outage.fillna(0, inplace=True)
ts_outage['DateTime'] = pd.to_datetime(ts_outage['DateTime'])
ts_outage.set_index('DateTime', drop=True, inplace=True)
# dim = ts_outage.shape
# ts_n = pd.DataFrame(data=np.tile(cluster_data['count'], (dim[0], 1)), index=ts_outage['DateTime'],
#                    columns=cluster_data.index)
# ts_avail = pd.DataFrame(data=np.tile(cluster_data['count'], (dim[0], 1)), index=ts_outage.index,
#                        columns=cluster_data.index) - ts_outage

df_tsexport = pd.merge(ts_load, ts_flows, how='outer', left_index=True, right_index=True)
df_tsexport = pd.merge(df_tsexport, ts_renew, how='outer', left_index=True, right_index=True)
df_tsexport = pd.merge(df_tsexport, ts_rescap, how='outer', left_index=True, right_index=True)
df_tsexport = pd.merge(df_tsexport, ts_hydro, how='outer', left_index=True, right_index=True)
df_tsexport = pd.merge(df_tsexport, ts_hydro_fill, how='outer', left_index=True, right_index=True)
df_tsexport = pd.merge(df_tsexport, ts_price_da, how='outer', left_index=True, right_index=True)
df_tsexport = pd.merge(df_tsexport, ts_prices, how='outer', left_index=True, right_index=True)
df_tsexport.to_csv(os.path.join(cfg.folder, 'data', 'medea_timeseries.csv'))
"""
