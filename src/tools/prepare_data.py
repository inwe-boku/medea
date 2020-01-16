# %% imports
import os

import numpy as np
import pandas as pd

import config as cfg
from src.tools.data_processing import hours_in_year

# TODO: PerformanceWarning: indexing past lexsort-depth may impact performance. need to sort index of affected
# dataframes. Possibly by reindex() or sort_index(). lexsort can be checked with df.index.is_lexsorted()

# --------------------------------------------------------------------------- #
# %% settings and initializing
# --------------------------------------------------------------------------- #
STATIC_FNAME = os.path.join(cfg.MEDEA_ROOT_DIR, 'data', 'processed', 'data_static.xlsx')
idx = pd.IndexSlice

# --------------------------------------------------------------------------- #
# %% read in data
# --------------------------------------------------------------------------- #

static_data = {
    'CAP_R': pd.read_excel(STATIC_FNAME, 'INITIAL_CAP_R', header=[0], index_col=[0, 1]),
    'CAPCOST_R': pd.read_excel(STATIC_FNAME, 'CAPITALCOST_R', header=[0], index_col=[0, 1]),
    'potentials': pd.read_excel(STATIC_FNAME, 'potentials', header=[0], index_col=[0]),
    'tec': pd.read_excel(STATIC_FNAME, 'parameters_G'),
    'feasops': pd.read_excel(STATIC_FNAME, 'FEASIBLE_INPUT-OUTPUT'),
    'cost_transport': pd.read_excel(STATIC_FNAME, 'COST_TRANSPORT', header=[0], index_col=[0]),
    'CAPCOST_K': pd.read_excel(STATIC_FNAME, 'CAPITALCOST_S', header=[0], index_col=[0, 1]),
    'CAP_X': pd.read_excel(STATIC_FNAME, 'ATC', index_col=[0]),
    'DISTANCE': pd.read_excel(STATIC_FNAME, 'KM', index_col=[0])
}

# --------------------------------------------------------------------------------------------------------------------

plant_data = {
    'hydro': pd.read_excel(os.path.join(cfg.MEDEA_ROOT_DIR, 'data', 'processed', 'plant-list_hydro.xlsx'),
                           'opsd_hydro'),
    'conventional': pd.read_excel(os.path.join(cfg.MEDEA_ROOT_DIR, 'data', 'processed', 'power_plant_db.xlsx'))
}

ts_data = {
    'timeseries': pd.read_csv(os.path.join(cfg.MEDEA_ROOT_DIR, 'data', 'processed', 'medea_regional_timeseries.csv'))
}

# --------------------------------------------------------------------------- #
# %% prepare set data
# --------------------------------------------------------------------------- #
dict_sets = {
    'f': {
        'Nuclear': [10],
        'Lignite': [20],
        'Coal': [30],
        'Gas': [40],
        'Oil': [50],
        'Hydro': [60],
        'Biomass': [70],
        'Solar': [80],
        'Wind': [90],
        'Power': [100],
        'Heat': [110],
        'Syngas': [120]
    },
    'l': {f'l{x}': [True] for x in range(1, 5)},
    'm': {
        'el': True,
        'ht': True
    },
    'n': {
        'pv': [True],
        'ror': [True],
        'wind_on': [True],
        'wind_off': [True]
    },
    'k': {
        'psp_day': [True],
        'psp_week': [True],
        'psp_season': [True],
        'res_day': [True],
        'res_week': [True],
        'res_season': [True],
        'battery': [True]
    },
    't': {f't{hour}': [True] for hour in range(1, hours_in_year(cfg.year) + 1)},
    'z': {zone: [True] for zone in cfg.zones}
}
# convert to DataFrames
for key, value in dict_sets.items():
    dict_sets.update({key: pd.DataFrame.from_dict(dict_sets[key], orient='index', columns=['Value'])})

# --------------------------------------------------------------------------- #
# %% prepare static data
# --------------------------------------------------------------------------- #
# Source 'CO2_INTENSITY': CO2 Emission Factors for Fossil Fuels, UBA, 2016
dict_static = {
    'CO2_INTENSITY': {
        'Nuclear': [0],
        'Lignite': [0.399],
        'Coal': [0.337],
        'Gas': [0.201],
        'Oil': [0.266],
        'Hydro': [0],
        'Biomass': [0],
        'Solar': [0],
        'Wind': [0],
        'Power': [0],
        'Heat': [0],
        'Syngas': [0]
    },
    'eta': {
        'nuc': [0.34],
        'lig_stm': [0.31], 'lig_stm_chp': [0.31],
        'lig_boa': [0.43], 'lig_boa_chp': [0.43],
        'coal_sub': [0.32], 'coal_sub_chp': [0.32],
        'coal_sc': [0.41], 'coal_sc_chp': [0.41],
        'coal_usc': [0.44], 'coal_usc_chp': [0.44],
        'coal_igcc': [0.55],
        'ng_stm': [0.40], 'ng_stm_chp': [0.40],
        'ng_cbt_lo': [0.34], 'ng_cbt_lo_chp': [0.34],
        'ng_cbt_hi': [0.40], 'ng_cbt_hi_chp': [0.40],
        'ng_cc_lo': [0.38], 'ng_cc_lo_chp': [0.38],
        'ng_cc_hi': [0.55], 'ng_cc_hi_chp': [0.55],
        'ng_mtr': [0.40], 'ng_mtr_chp': [0.40],
        'ng_boiler_chp': [0.90],
        'oil_stm': [0.31], 'oil_stm_chp': [0.31],
        'oil_cbt': [0.35], 'oil_cbt_chp': [0.35],
        'oil_cc': [0.42], 'oil_cc_chp': [0.42],
        'bio': [0.35], 'bio_chp': [0.35],
        'heatpump_pth': [3.0]
    },
    'map_name2fuel': {
        'nuc': 'Nuclear',
        'lig': 'Lignite',
        'coal': 'Coal',
        'ng': 'Gas',
        'oil': 'Oil',
        'bio': 'Biomass',
        'heatpump': 'Power'
    },
    'CAPCOST_X': {
        'AT': [1250],
        'DE': [1250]
    },
    'VALUE_NSE': {
        'AT': [12500],
        'DE': [12500]
    },
    'LAMBDA': [0.125],
    'SIGMA': [0.175]
}

dict_additions = {
    'boilers': {
        'medea_type': [49.5],
        ('cap', 'AT'): [4.5],
        ('cap', 'DE'): [25.5],
        ('eta', 'AT'): [0.9],
        ('eta', 'DE'): [0.9],
        ('count', 'AT'): [15],
        ('count', 'DE'): [85],
        ('num', 'AT'): [85],
        ('num', 'DE'): [255]
    },
    'heatpumps': {
        'medea_type': [100],
        ('cap', 'AT'): [0.1],
        ('cap', 'DE'): [0.1],
        ('eta', 'AT'): [3.0],
        ('eta', 'DE'): [3.0],
        ('count', 'AT'): [1],
        ('count', 'DE'): [1],
        ('num', 'AT'): [1],
        ('num', 'DE'): [1]
    },
    'batteries': {
        'power_in': [0],
        'power_out': [0],
        'energy_max': [0],
        'efficiency_in': [0.96],
        'efficiency_out': [0.96],
        'cost_power': [static_data['CAPCOST_K'].loc[('AT', 'battery'), 'annuity-power'].round(4)],
        'cost_energy': [static_data['CAPCOST_K'].loc[('AT', 'battery'), 'annuity-energy'].round(4)],
        'inflow_factor': [0]
    }
}

dict_instantiate = {'CO2_INTENSITY': pd.DataFrame.from_dict(dict_static['CO2_INTENSITY'],
                                                                 orient='index', columns=['Value'])}

dict_instantiate.update({'efficiency': pd.DataFrame.from_dict(dict_static['eta'], orient='index', columns=['l1'])})
dict_instantiate['efficiency']['product'] = 'el'
dict_instantiate['efficiency'].loc[dict_instantiate['efficiency'].index.str.contains('pth'), 'product'] = 'ht'
dict_instantiate['efficiency'].loc['ng_boiler_chp', 'product'] = 'ht'
dict_instantiate['efficiency']['fuel'] = dict_instantiate['efficiency'].index.to_series().str.split('_').str.get(
    0).replace(dict_static['map_name2fuel'])
dict_instantiate['efficiency'].set_index(['product', 'fuel'], append=True, inplace=True)
dict_instantiate['efficiency'].index.set_names(['medea_type', 'product', 'fuel_name'], inplace=True)
for i in range(1, 6):
    dict_instantiate['efficiency'][f'l{i}'] = dict_instantiate['efficiency']['l1']

dict_instantiate.update({'CAP_R': static_data['CAP_R'].loc[idx[:, cfg.year], :]})
dict_instantiate.update({'CAP_X': static_data['CAP_X'].loc[static_data['CAP_X'].index.str.contains('|'.join(cfg.zones)),
                                                       static_data['CAP_X'].columns.str.contains('|'.join(cfg.zones))] /
                                1000})
dict_instantiate.update({'DISTANCE': static_data['DISTANCE'].loc[static_data['DISTANCE'].index.str.contains(
    '|'.join(cfg.zones)), static_data['DISTANCE'].columns.str.contains('|'.join(cfg.zones))]})

static_data.update({'CAPCOST_X': pd.DataFrame.from_dict(dict_static['CAPCOST_X'], orient='index', columns=['Value'])})
static_data.update({'VALUE_NSE': pd.DataFrame.from_dict(dict_static['VALUE_NSE'], orient='index', columns=['Value'])})
static_data.update({'LAMBDA': pd.DataFrame(dict_static['LAMBDA'], columns=['Value'])})
static_data.update({'SIGMA': pd.DataFrame(dict_static['SIGMA'], columns=['Value'])})

# --------------------------------------------------------------------------- #
# %% preprocessing plant data
# --------------------------------------------------------------------------- #
# select active thermal plants
plant_data.update({'active': plant_data['conventional'].loc[
    (plant_data['conventional']['UnitOperOnlineDate'] < pd.Timestamp(cfg.year, 1, 1)) &
    (plant_data['conventional']['UnitOperRetireDate'] > pd.Timestamp(cfg.year, 12, 31)) |
    np.isnat(plant_data['conventional']['UnitOperRetireDate'])
    ]})
plant_data['active'] = plant_data['active'].loc[
    (plant_data['active']['MedeaType'] < 60) |
    (plant_data['active']['MedeaType'] >= 70)
    ]

# distinguish between plants in different countries
tec_props = plant_data['active'].groupby(['MedeaType', 'PlantCountry'])['UnitNameplate'].sum().to_frame() / 1000
tec_props['eta'] = plant_data['active'].groupby(['MedeaType', 'PlantCountry'])['Eta'].mean().to_frame()
tec_props['count'] = plant_data['active'].groupby(['MedeaType'])['PlantCountry'].value_counts().to_frame(name='count')
tec_props['num'] = (tec_props['UnitNameplate'].round(decimals=1) * 10).astype(int)
tec_props.rename(index={'Germany': 'DE', 'Austria': 'AT'}, columns={'UnitNameplate': 'cap'}, inplace=True)
tec_props = tec_props.unstack(-1)
tec_props.drop(0.0, axis=0, inplace=True)
# add data for heat boilers
tec_props = tec_props.append(pd.DataFrame.from_dict(dict_additions['boilers']).set_index('medea_type'))
# add data for heatpumps
tec_props = tec_props.append(pd.DataFrame.from_dict(dict_additions['heatpumps']).set_index('medea_type'))
# tec_props.drop(0, axis=0, inplace=True)

# TODO: Throws SettingWithCopyWarning: A value is trying to be set on a copy of a slice from a DataFrame
for zone in cfg.zones:
    tec_props.loc[:, 'eta'].update(pd.DataFrame.from_dict(dict_static['eta'], orient='index', columns=[zone]),
                                   overwrite=False)
# index by plant element names instead of medea_type-numbers
# TODO: massive error when matching medea-numbers to plant names
type_plant_match = static_data['tec'][['medea_type', 'set_element']].copy()
type_plant_match.set_index('medea_type', inplace=True)
tec_props['set_elements'] = type_plant_match.loc[tec_props.index, :].values
tec_props.set_index('set_elements', inplace=True)
tec_props = tec_props.stack(-1).swaplevel(axis=0)
tec_props = tec_props.dropna()
dict_instantiate.update({'tec_props': tec_props})

# add 'tec'-set to dict_sets
dict_sets.update({'i': pd.DataFrame(data=True, index=tec_props.index.get_level_values(1).unique().values,
                                      columns=['Value'])})

static_data['feasops']['fuel_name'] = (static_data['feasops']['medea_type'] / 10).apply(np.floor) * 10
static_data['feasops']['fuel_name'].replace({y: x for x, y in dict_sets['f'].itertuples()}, inplace=True)
static_data['feasops']['set_element'] = static_data['feasops']['medea_type']
static_data['feasops']['set_element'].replace(
    {x: y for x, y in static_data['tec'][['medea_type', 'set_element']].values}, inplace=True)
static_data['feasops'].dropna(inplace=True)
static_data['feasops'].set_index(['set_element', 'l', 'fuel_name'], inplace=True)
# following line produces memory error (0xC00000FD) --> workaround with element-wise division
# df_feasops['fuel_need'] = df_feasops['fuel']/ df_eff
# TODO: PerformanceWarning: indexing past lexsort depth may impact performance
static_data['feasops']['fuel_need'] = np.nan
for typ in static_data['feasops'].index.get_level_values(0).unique():
    for lim in static_data['feasops'].index.get_level_values(1).unique():
        static_data['feasops'].loc[idx[typ, lim], 'fuel_need'] = static_data['feasops'].loc[
                                                                     idx[typ, lim], 'fuel'].mean() / \
                                                                 dict_static['eta'][typ][0]

# adjust static_data['tec'] to reflect modelled power plants
static_data['tec'].set_index('set_element', inplace=True)
static_data['tec'] = static_data['tec'].loc[static_data['tec'].index.isin(dict_sets['i'].index), :]
dict_instantiate['efficiency'] = \
    dict_instantiate['efficiency'].loc[
    dict_instantiate['efficiency'].index.get_level_values(0).isin(dict_sets['i'].index), :]
static_data['feasops'] = \
    static_data['feasops'].loc[static_data['feasops'].index.get_level_values(0).isin(dict_sets['i'].index), :]

# --------------------------------------------------------------------------- #
# hydro storage data
# drop all ror data
plant_data['hydro'].drop(plant_data['hydro'][plant_data['hydro'].technology == 'Run-of-river'].index, inplace=True)
# filter out data without reservoir size in GWh
plant_data['hydro'].dropna(subset=['energy_max', 'power_in'], inplace=True)
# calculate duration of generation from full reservoir
plant_data['hydro']['max_duration'] = plant_data['hydro']['energy_max'] / plant_data['hydro']['power_out'] * 1000 / 24
plant_data['hydro']['count'] = 1
plant_data.update({'hydro_clusters': plant_data['hydro'].groupby(['technology', 'country',
                                                                  pd.cut(plant_data['hydro']['max_duration'],
                                                                         [0, 2, 7, 75])]).sum()})
plant_data['hydro_clusters']['efficiency_in'] = plant_data['hydro_clusters']['efficiency_in'] / \
                                                plant_data['hydro_clusters']['count']
plant_data['hydro_clusters']['efficiency_out'] = plant_data['hydro_clusters']['efficiency_out'] / \
                                                 plant_data['hydro_clusters']['count']
plant_data['hydro_clusters']['cost_power'] = np.nan
plant_data['hydro_clusters']['cost_energy'] = np.nan
# assign technology and zone index to rows
plant_data['hydro_clusters']['country'] = plant_data['hydro_clusters'].index.get_level_values(1)
plant_data['hydro_clusters']['category'] = plant_data['hydro_clusters'].index.get_level_values(2).rename_categories(
    ['day', 'week', 'season']).astype(str)
plant_data['hydro_clusters']['tech'] = plant_data['hydro_clusters'].index.get_level_values(0)
plant_data['hydro_clusters']['tech'] = plant_data['hydro_clusters']['tech'].replace(['Pumped Storage', 'Reservoir'],
                                                                                    ['psp', 'res'])
plant_data['hydro_clusters']['set_elem'] = plant_data['hydro_clusters']['tech'] + '_' + plant_data['hydro_clusters'][
    'category']
plant_data['hydro_clusters'] = plant_data['hydro_clusters'].set_index(['set_elem', 'country'])
plant_data['hydro_clusters'].fillna(0, inplace=True)
plant_data['hydro_clusters']['power_out'] = plant_data['hydro_clusters']['power_out'] / 1000  # conversion from MW to GW
plant_data['hydro_clusters']['power_in'] = plant_data['hydro_clusters']['power_in'] / 1000  # conversion from MW to GW
plant_data['hydro_clusters']['inflow_factor'] = (
        plant_data['hydro_clusters']['energy_max'] / plant_data['hydro_clusters']['energy_max'].sum())
plant_data['hydro_clusters'] = plant_data['hydro_clusters'].loc[:, ['power_in', 'power_out', 'energy_max',
                                                                    'efficiency_in', 'efficiency_out', 'cost_power',
                                                                    'cost_energy', 'inflow_factor']].copy()
# append battery data
bat_idx = pd.MultiIndex.from_product([['battery'], list(cfg.zones)])
df_battery = pd.DataFrame(np.nan, bat_idx, dict_additions['batteries'].keys())
for zone in list(cfg.zones):
    for key in dict_additions['batteries'].keys():
        df_battery.loc[('battery', zone), key] = dict_additions['batteries'][key][0]

plant_data['storage_clusters'] = plant_data['hydro_clusters'].append(df_battery)

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

dict_instantiate.update({'ancil': ts_data['zonal'].loc[:, idx[:, 'el', 'load']].max().unstack((1, 2)).squeeze() * 0.125
                                  + dict_instantiate['CAP_R'].unstack(1).drop('ror', axis=1).sum(axis=1) * 0.075})
dict_instantiate.update({'PEAK_LOAD': ts_data['zonal'].loc[:, idx[:, 'el', 'load']].max().unstack((1, 2)).squeeze()})
dict_instantiate.update({'PEAK_PROFILE': ts_data['zonal'].loc[:, idx[:, :, 'profile']].max().unstack(2).drop(
    'ror', axis=0, level=1)})

# drop rows with all zeros
plant_data['storage_clusters'] = \
    plant_data['storage_clusters'].loc[~(plant_data['storage_clusters'] == 0).all(axis=1), :].copy()

# --------------------------------------------------------------------------- #
# %% limits on investment - long-run vs short-run & # TODO: potentials
# --------------------------------------------------------------------------- #
invest_limits = {}

lim_invest_thermal = pd.DataFrame([0])
if cfg.invest_conventionals:
    lim_invest_thermal = pd.DataFrame([float('inf')])
invest_limits.update({'thermal': lim_invest_thermal})

# dimension lim_invest_itm[r, tec_itm]
lim_invest_itm = pd.DataFrame(data=0, index=cfg.zones, columns=dict_sets['n'].index)
if cfg.invest_renewables:
    for zone in cfg.zones:
        for itm in lim_invest_itm.columns:
            lim_invest_itm.loc[zone, itm] = float(static_data['potentials'].loc[itm, zone])
invest_limits.update({'intermittent': lim_invest_itm})

# dimension lim_invest_storage[r, tec_strg]
lim_invest_storage = pd.DataFrame(data=0, index=cfg.zones, columns=dict_sets['k'].index)
if cfg.invest_storage:
    for zone in cfg.zones:
        for strg in lim_invest_storage.columns:
            lim_invest_storage.loc[zone, strg] = float(static_data['potentials'].loc[strg, zone])
invest_limits.update({'storage': lim_invest_storage})

# dimension lim_invest_atc[r,rr]
lim_invest_atc = pd.DataFrame(data=0, index=cfg.zones, columns=cfg.zones)
if cfg.invest_tc:
    for zone in cfg.zones:
        lim_invest_atc.loc[zone, lim_invest_atc.index.difference([zone])] = 1
invest_limits.update({'atc': lim_invest_atc})
