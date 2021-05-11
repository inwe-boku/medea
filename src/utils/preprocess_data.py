# %% imports
import numpy as np
import pandas as pd

import config as cfg
from src.utils.data_processing import hours_in_year, medea_path

# --------------------------------------------------------------------------- #
# %% settings and initializing
# --------------------------------------------------------------------------- #
STATIC_FNAME = medea_path('data', 'processed', 'data_static.xlsx')
idx = pd.IndexSlice

# --------------------------------------------------------------------------- #
# %% Read Data
plant_data = {
    'technology': pd.read_excel(STATIC_FNAME, 'Technologies', header=[2], index_col=[2]).dropna(axis=0, how='all'),
    'chp': pd.read_excel(STATIC_FNAME, 'FEASIBLE_INPUT-OUTPUT', header=[0], index_col=[0, 1, 2]),
    'installed': pd.read_excel(STATIC_FNAME, 'Capacities', header=[0, 1], index_col=[0, 1, 2], skiprows=[0, 1, 2]),
    'CAP_X': pd.read_excel(STATIC_FNAME, 'ATC', index_col=[0]),
    'DISTANCE': pd.read_excel(STATIC_FNAME, 'KM', index_col=[0])
}

ts_data = {
    'timeseries': pd.read_csv(medea_path('data', 'processed', 'medea_regional_timeseries.csv'))
}

estimates = {
    'ESTIMATES': pd.read_excel(STATIC_FNAME, 'ESTIMATES', index_col=[0]),
    'VALUE_NSE': pd.read_excel(STATIC_FNAME, 'VALUE_NSE', index_col=[0]),
    'AIR_POLLUTION': pd.read_excel(STATIC_FNAME, 'AIR_POLLUTION', index_col=[0]),
    'CO2_INTENSITY': pd.read_excel(STATIC_FNAME, 'CO2_INTENSITY', index_col=[0]),
    'COST_TRANSPORT': pd.read_excel(STATIC_FNAME, 'COST_TRANSPORT', index_col=[0]),
    'DISCOUNT_RATE': pd.read_excel(STATIC_FNAME, 'WACC', index_col=[0])
}

# --------------------------------------------------------------------------- #
# %% create dict_sets

dict_sets = {
    't': {all_tec: [True] for all_tec in plant_data['technology'].index},
    'i': {fuel: [True] for fuel in np.append(plant_data['technology'].loc[:, 'fuel'].unique(), np.array(['ch4']))},
    'd': {plant: [True] for plant in plant_data['technology'].loc[
        plant_data['technology']['conventional'] == 1].index.unique()},
    's': {storage: [True] for storage in plant_data['technology'].loc[
        plant_data['technology']['storage'] == 1].index.unique()},
    'l': {f'l{x}': [True] for x in range(1, 5)},
    'f': {'el': True, 'ht': True, 'h2': True, 'ch4': True},
    'r': {intmit: [True] for intmit in plant_data['technology'].loc[
        plant_data['technology']['intermittent'] == 1].index.unique()},
    'h': {f'h{hour}': [True] for hour in range(1, hours_in_year(cfg.year) + 1)},
    'z': {zone: [True] for zone in cfg.zones}
}

# convert to DataFrames
for key, value in dict_sets.items():
    dict_sets.update({key: pd.DataFrame.from_dict(dict_sets[key], orient='index', columns=['Value'])})

# --------------------------------------------------------------------------- #
# %% chp fuel need
# --------------------------------------------------------------------------- #
plant_data['chp']['fuel_need'] = plant_data['chp']['fuel'] / plant_data['technology'].loc[
    plant_data['technology']['heat_generation'] == 1, 'eta_ec']

# --------------------------------------------------------------------------- #
# %% compile capacities
# --------------------------------------------------------------------------- #


# --------------------------------------------------------------------------- #
# %% transmission capacities and distances
# --------------------------------------------------------------------------- #
# add fuel for transmission capacities
plant_data.update({'CAP_X':
                       plant_data['CAP_X'].stack().to_frame().assign(f='el').set_index('f', append=True).unstack(1)})

plant_data.update({'CAP_X':
                       plant_data['CAP_X'].loc[
                           plant_data['CAP_X'].index.get_level_values(0).str.contains('|'.join(cfg.zones)),
                           plant_data['CAP_X'].columns.get_level_values(1).str.contains('|'.join(cfg.zones))] / 1000})

plant_data.update({'DISTANCE': plant_data['DISTANCE'].loc[
    plant_data['DISTANCE'].index.str.contains('|'.join(cfg.zones)),
    plant_data['DISTANCE'].columns.str.contains('|'.join(cfg.zones))]})

# --------------------------------------------------------------------------- #
# %% process time series data
# --------------------------------------------------------------------------- #
ts_data['timeseries']['DateTime'] = pd.to_datetime(ts_data['timeseries']['DateTime'])
ts_data['timeseries'].set_index('DateTime', inplace=True)
# constrain data to scenario year
ts_data['timeseries'] = ts_data['timeseries'].loc[
    (pd.Timestamp(cfg.year, 1, 1, 0, 0).tz_localize('UTC') <= ts_data['timeseries'].index) &
    (ts_data['timeseries'].index <= pd.Timestamp(cfg.year, 12, 31, 23, 0).tz_localize('UTC'))]

# drop index and set index of df_time instead
if len(ts_data['timeseries']) == len(dict_sets['h']):
    ts_data['timeseries'].set_index(dict_sets['h'].index, inplace=True)
else:
    raise ValueError('Mismatch of time series data and model time resolution. Is cfg.year wrong?')

ts_data['timeseries']['DE-power-load'] = ts_data['timeseries']['DE-power-load'] / 0.91
# TODO: re-check scaling factor
# for 0.91 scaling factor see
# https://www.entsoe.eu/fileadmin/user_upload/_library/publications/ce/Load_and_Consumption_Data.pdf

# create price time series incl transport cost
ts_data['timeseries'].loc[:, 'Nuclear'] = 3.5
ts_data['timeseries'].loc[:, 'Lignite'] = 4.5
ts_data['timeseries'].loc[:, 'Biomass'] = 6.5

# subset of zonal time series
ts_data['ZONAL'] = ts_data['timeseries'].loc[:, ts_data['timeseries'].columns.str.startswith(tuple(cfg.zones))].copy()
ts_data['ZONAL'].columns = ts_data['ZONAL'].columns.str.split('-', expand=True)
# adjust column naming to reflect proper product names ('el' and 'ht')
ts_data['ZONAL'] = ts_data['ZONAL'].rename(columns={'power': 'el', 'heat': 'ht'})

model_prices = ['Coal', 'Oil', 'Gas', 'EUA', 'Nuclear', 'Lignite', 'Biomass', 'price_day_ahead']
ts_data['price'] = pd.DataFrame(index=ts_data['timeseries'].index,
                                columns=pd.MultiIndex.from_product([model_prices, cfg.zones]))

for zone in cfg.zones:
    for fuel in model_prices:
        if fuel in estimates['COST_TRANSPORT'].index:
            ts_data['price'][(fuel, zone)] = ts_data['timeseries'][fuel] + estimates['COST_TRANSPORT'].loc[fuel, zone]
        else:
            ts_data['price'][(fuel, zone)] = ts_data['timeseries'][fuel]

# Inflows to hydro storage plant
hydro_storage = plant_data['technology'].loc[(plant_data['technology']['storage'] == 1) &
                                             (plant_data['technology']['fuel'] == 'Water')].index

inflow_factor = plant_data['installed'].loc[idx['Installed Capacity Out', :, cfg.year], hydro_storage].T / \
                plant_data['installed'].loc[idx['Installed Capacity Out', :, cfg.year], hydro_storage].T.sum()
inflow_factor.columns = inflow_factor.columns.droplevel([0, 2])

ts_inflows = pd.DataFrame(index=list(ts_data['ZONAL'].index),
                          columns=pd.MultiIndex.from_product([cfg.zones, dict_sets['s'].index]))

for zone in list(cfg.zones):
    for strg in hydro_storage:
        ts_inflows.loc[:, (zone, strg)] = ts_data['ZONAL'].loc[:, idx[zone, 'inflows', 'reservoir']] * \
                                          inflow_factor.loc[strg, zone]
ts_data.update({'INFLOWS': ts_inflows})

# --------------------------------------------------------------------------- #
# %% peak load and profiles
# --------------------------------------------------------------------------- #
ts_data.update({'PEAK_LOAD': ts_data['ZONAL'].loc[:, idx[:, 'el', 'load']].max().unstack((1, 2)).squeeze()})
peak_profile = ts_data['ZONAL'].loc[:, idx[:, :, 'profile']].max().unstack(2).drop('ror', axis=0, level=1)
peak_profile.fillna(0, inplace=True)
ts_data.update({'PEAK_PROFILE': peak_profile})

# --------------------------------------------------------------------------- #
# %% limits on investment - long-run vs short-run
# TODO: set limits to potentials -- requires potentials first
# --------------------------------------------------------------------------- #
invest_limits = {
    'potentials': pd.read_excel(STATIC_FNAME, 'potentials', index_col=[0]),
    'thermal': pd.DataFrame([float('inf') if cfg.invest_conventionals else 0]),
    'intermittent': pd.DataFrame(data=[float('inf') if cfg.invest_renewables else 0][0],
                                 index=cfg.zones, columns=dict_sets['r'].index),
    'storage': pd.DataFrame(data=[float('inf') if cfg.invest_storage else 0][0],
                            index=cfg.zones, columns=dict_sets['s'].index),
    'atc': pd.DataFrame(data=[1 if cfg.invest_tc else 0][0],
                        index=cfg.zones, columns=cfg.zones)
}
