# %% imports
import os

import numpy as np
import pandas as pd

import config as cfg
from src.tools.data_processing import hours_in_year

# --------------------------------------------------------------------------- #
# %% settings and initializing
# --------------------------------------------------------------------------- #
STATIC_FNAME = os.path.join(cfg.MEDEA_ROOT_DIR, 'data', 'processed', 'data_static.xlsx')
idx = pd.IndexSlice

### ### ### processes data and writes: dict_sets, dict_instantiate, static_data, plant_data, ts_data, invest_limits
###
### dict_sets includes: f, i, l, m, n, k, t, z
### dict_instantiate includes:  'efficiency', 'DISTANCE', 'tec_props', 'ancil',
#
### static_data includes:       'potentials', 'tec', 'feasops', 'cost_transport',
#
### plant_data includes:        'hydro', 'conventional', 'active', 'hydro_clusters', 'storage_clusters'
### ts_data includes:           'timeseries', 'zonal', 'price', 'inflows'
### invest_limits includes:     'thermal', 'intermittent', 'storage', 'atc'

# 'CAP_G', 'CAP_R', 'CAP_S_OUT', 'CAP_S_IN', 'CAP_V', 'CAP_X', 'CAPCOST_R', 'CAPCOST_K', 'CAPCOST_X',
# 'EFFICIENCY_G', 'EFFICIENCY_S_OUT', 'EFFICIENCY_S_IN'
#
# 'FEASIBLE_INPUT', 'FEASIBLE_OUTPUT'
#
# 'OM_COST_G_QFIX', 'OM_COST_G_VAR', 'OM_COST_R_QFIX', 'OM_COST_R_VAR'
#
# 'AIR_POLLUTION', 'VALUE_NSE', 'LAMBDA', 'SIGMA', 'CO2_INTENSITY', 'PEAK_LOAD', 'PEAK_PROFILE', VALUE_NSE
#
# 'DEMAND', 'GEN_PROFILE', 'INFLOWS',

# INITIAL_CAP_G, INITIAL_CAP_R, INITIAL_CAP_S_OUT, INITIAL_CAP_S_IN, INITIAL_CAP_V, INITIAL_CAP_X

# OM_COST_G_QFIX, OM_COST_G_VAR, OM_COST_R_QFIX, OM_COST_R_VAR,
# AIR_POL_COST_FIX, AIR_POL_COST_VAR
# PRICE_CO2, PRICE_FUEL, PRICE_DA,
# --------------------------------------------------------------------------- #
# %% Read Data
plant_data = {
    'technology': pd.read_excel(STATIC_FNAME, 'Technologies', header=[2], index_col=[2]),
    'chp': pd.read_excel(STATIC_FNAME, 'FEASIBLE_INPUT-OUTPUT', header=[0], index_col=[0, 1, 2]),
    'installed': pd.read_excel(STATIC_FNAME, 'Capacities', header=[0], index_col=[0, 1, 2], skiprows=[0, 1, 2])
}

# technology_data = pd.read_excel(STATIC_FNAME, 'Technologies', header=[2], index_col=[2])
# chp_data = pd.read_excel(STATIC_FNAME, 'FEASIBLE_INPUT-OUTPUT', header=[0], index_col=[0, 1])
ts_data = {
    'timeseries': pd.read_csv(os.path.join(cfg.MEDEA_ROOT_DIR, 'data', 'processed', 'medea_regional_timeseries.csv'))
}

# --------------------------------------------------------------------------- #
# %% create dict_sets
### dict_sets includes: f, i, l, m, n, k, t, z

dict_sets = {
    'f': {fuel: [True] for fuel in plant_data['technology'].loc[:, 'fuel'].unique()},
    'i': {plant: [True] for plant in plant_data['technology'].loc[
        plant_data['technology']['intermittent'] == 0].index.unique()},
    'k': {storage: [True] for storage in plant_data['technology'].loc[
        plant_data['technology']['storage'] == 1].index.unique()},
    'l': {f'l{x}': [True] for x in range(1, 5)},
    'm': {'el': True, 'ht': True},
    'n': {intmit: [True] for intmit in plant_data['technology'].loc[
        plant_data['technology']['intermittent'] == 1].index.unique()},
    't': {f't{hour}': [True] for hour in range(1, hours_in_year(cfg.year) + 1)},
    'z': {zone: [True] for zone in cfg.zones}
}

# --------------------------------------------------------------------------- #
# %% chp fuel need
# --------------------------------------------------------------------------- #
plant_data['chp']['fuel_need'] = plant_data['chp']['fuel'] / plant_data['technology'].loc[
    plant_data['technology']['heat_generation'] == 1, 'eta_ec']

# --------------------------------------------------------------------------- #
# %% compile capacities
# --------------------------------------------------------------------------- #


# --------------------------------------------------------------------------- #
# %% process time series data
# --------------------------------------------------------------------------- #
# ts_medea = pd.read_csv(os.path.join(cfg.folder, 'medea', 'data', 'processed', 'medea_regional_timeseries.csv'))
ts_data['timeseries']['DateTime'] = pd.to_datetime(ts_data['timeseries']['DateTime'])
ts_data['timeseries'].set_index('DateTime', inplace=True)
# constrain data to scenario year
ts_data['timeseries'] = ts_data['timeseries'].loc[
    (pd.Timestamp(cfg.year, 1, 1, 0, 0).tz_localize('UTC') <= ts_data['timeseries'].index) & (
            ts_data['timeseries'].index <= pd.Timestamp(cfg.year, 12, 31, 23, 0).tz_localize('UTC'))]
# drop index and set index of df_time instead
if len(ts_data['timeseries']) == len(dict_sets['t']):
    ts_data['timeseries'].set_index(dict_sets['t'].index, inplace=True)
else:
    raise ValueError('Mismatch of time series data and model time resolution. Is cfg.year wrong?')
ts_data['timeseries']['DE-power-load'] = ts_data['timeseries']['DE-power-load'] / 0.91
# for 0.91 scaling factor see
# https://www.entsoe.eu/fileadmin/user_upload/_library/publications/ce/Load_and_Consumption_Data.pdf

# create price time series incl transport cost
ts_data['timeseries']['Nuclear'] = 3.5
ts_data['timeseries']['Lignite'] = 4.5
ts_data['timeseries']['Biomass'] = 6.5

# subset of zonal time series
ts_data['zonal'] = ts_data['timeseries'].loc[:, ts_data['timeseries'].columns.str.startswith(('AT', 'DE'))].copy()
ts_data['zonal'].columns = ts_data['zonal'].columns.str.split('-', expand=True)
# adjust column naming to reflect proper product names ('el' and 'ht')
ts_data['zonal'] = ts_data['zonal'].rename(columns={'power': 'el', 'heat': 'ht'})

model_prices = ['Coal', 'Oil', 'Gas', 'EUA', 'Nuclear', 'Lignite', 'Biomass', 'price_day_ahead']

ts_data['price'] = pd.DataFrame(index=ts_data['timeseries'].index,
                                columns=pd.MultiIndex.from_product([model_prices, cfg.zones]))
for zone in cfg.zones:
    for fuel in model_prices:
        if fuel in static_data['cost_transport'].index:
            ts_data['price'][(fuel, zone)] = ts_data['timeseries'][fuel] + static_data['cost_transport'].loc[fuel, zone]
        else:
            ts_data['price'][(fuel, zone)] = ts_data['timeseries'][fuel]

ts_inflows = pd.DataFrame(index=list(ts_data['zonal'].index),
                          columns=pd.MultiIndex.from_product([cfg.zones, dict_sets['k'].index]))
for zone in list(cfg.zones):
    for strg in dict_sets['k'].index:
        if 'battery' not in strg:
            ts_inflows.loc[:, (zone, strg)] = ts_data['zonal'].loc[:, idx[zone, 'inflows', 'reservoir']] * \
                                              plant_data['storage_clusters'].loc[(strg, zone), 'inflow_factor']
ts_data.update({'inflows': ts_inflows})
