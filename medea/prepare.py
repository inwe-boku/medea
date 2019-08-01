import os

import numpy as np
import pandas as pd

import config as cfg
from medea.helpers import is_leapyear

#TODO: PerformanceWarning: indexing past lexsort-depth may impact performance. need to sort index of affected
# dataframes. Possibly by reindex() or sort_index(). lexsort can be checked with df.index.is_lexsorted()

# --------------------------------------------------------------------------- #
# %% settings and initializing
# --------------------------------------------------------------------------- #
idx = pd.IndexSlice

# --------------------------------------------------------------------------- #
# %% prepare set data
# --------------------------------------------------------------------------- #
fuel_set = {'Nuclear': 10, 'Lignite': 20, 'Coal': 30, 'Gas': 40, 'Oil': 50, 'Hydro': 60,
            'Biomass': 70, 'Solar': 80, 'Wind': 90, 'Power': 100, 'Heat': 110}
df_fuel = pd.DataFrame(fuel_set.values(), fuel_set.keys(), ['Value'])
df_lim = pd.DataFrame(data=True, index=[f'l{x}' for x in range(1, 6)], columns=['Value'])
df_prd = pd.DataFrame(data=True, index=['el', 'ht'], columns=['Value'])
df_props = pd.DataFrame(data=True, index=['power_out', 'power_in', 'energy_max', 'efficiency_out', 'efficiency_in',
                                          'cost_power', 'cost_energy'], columns=['Value'])
df_zones = pd.DataFrame(data=True, index=cfg.zones, columns=['Value'])
df_tec_itm = pd.DataFrame(data=True, index=['pv', 'ror', 'wind_on', 'wind_off'], columns=['Value'])
df_tec_strg = pd.DataFrame(data=True, index=['psp_day', 'psp_week', 'psp_season', 'res_day', 'res_week', 'res_season',
                                             'battery'], columns=['Value'])
if is_leapyear(cfg.year):
    df_time = pd.DataFrame({f't{hour}': True for hour in range(1, 8785)}.values(),
                           index={f't{hour}': True for hour in range(1, 8785)}.keys(), columns=['Value'])
else:
    df_time = pd.DataFrame({f't{hour}': True for hour in range(1, 8761)}.values(),
                           index={f't{hour}': True for hour in range(1, 8761)}.keys(), columns=['Value'])

# --------------------------------------------------------------------------- #
# %% prepare static data
# --------------------------------------------------------------------------- #
emission_intensity = {'Nuclear': 0, 'Lignite': 0.45, 'Coal': 0.333, 'Gas': 0.199, 'Oil': 0.275, 'Hydro': 0,
                      'Biomass': 0, 'Solar': 0, 'Wind': 0, 'Power': 0, 'Heat': 0}
df_emission_intensity = pd.DataFrame(emission_intensity.values(), emission_intensity.keys(), columns=['Value'])

efficiency_electric = {'nuc': 0.34, 'lig_stm': 0.33, 'lig_stm_chp': 0.33, 'lig_boa': 0.43, 'lig_boa_chp': 0.43,
                       'coal_sub': 0.35, 'coal_sub_chp': 0.35, 'coal_sc': 0.40, 'coal_sc_chp': 0.40, 'coal_usc': 0.44,
                       'coal_usc_chp': 0.44, 'coal_igcc': 0.40, 'ng_stm': 0.40, 'ng_stm_chp': 0.40, 'ng_cbt_lo': 0.33,
                       'ng_cbt_lo_chp': 0.33, 'ng_cbt_hi': 0.40, 'ng_cbt_hi_chp': 0.40, 'ng_cc_lo': 0.38,
                       'ng_cc_lo_chp': 0.38, 'ng_cc_hi': 0.55, 'ng_cc_hi_chp': 0.55, 'ng_mtr': 0.40, 'ng_mtr_chp': 0.40,
                       'ng_boiler_chp': 0.90, 'oil_stm': 0.31, 'oil_stm_chp': 0.31, 'oil_cbt': 0.35,
                       'oil_cbt_chp': 0.35, 'oil_cc': 0.42, 'oil_cc_chp': 0.42, 'hyd_ror': 0.98, 'hyd_res': 0.94,
                       'hyd_psp': 0.8, 'bio': 0.35, 'bio_chp': 0.35, 'heatpump_pth': 3.0}
df_efficiency = pd.DataFrame.from_dict(efficiency_electric, orient='index', columns=['l1'])
dict_name2fuel = {'nuc': 'Nuclear', 'lig': 'Lignite', 'coal': 'Coal', 'ng': 'Gas', 'oil': 'Oil', 'bio': 'Biomass',
                  'heatpump': 'Power'}
df_efficiency['product'] = 'el'
df_efficiency.loc[df_efficiency.index.str.contains('pth'), 'product'] = 'ht'
df_efficiency['fuel'] = df_efficiency.index.to_series().str.split('_').str.get(0).replace(dict_name2fuel)
df_efficiency.set_index(['product', 'fuel'], append=True, inplace=True)
df_efficiency.index.set_names(['medea_type', 'product', 'fuel_name'], inplace=True)
for i in range(1, 6):
    df_efficiency[f'l{i}'] = df_efficiency['l1']
df_efficiency.drop('hyd', level='fuel_name', inplace=True)

# TODO: include efficiencies for heat generation in case of chps?

# --------------------------------------------------------------------------- #
# %% data inputs
# --------------------------------------------------------------------------- #
data_itm_cap = pd.read_excel(os.path.join(cfg.folder, 'medea', 'data', 'processed', 'data_static.xlsx'),
                             'installed_itm', header=[0, 1], index_col=[0])
df_itm_cap = data_itm_cap.loc[cfg.year, :]

df_itm_invest = pd.read_excel(os.path.join(cfg.folder, 'medea', 'data', 'processed', 'data_static.xlsx'),
                              'invest_itm', header=[0, 1], index_col=[0])

data_technology = pd.read_excel(os.path.join(cfg.folder, 'medea', 'data', 'processed', 'data_static.xlsx'),
                                'param_thermal')

data_feasops = pd.read_excel(os.path.join(cfg.folder, 'medea', 'data', 'processed', 'data_static.xlsx'),
                             'feasgen_thermal')

data_technology.set_index('set_element', inplace=True)
data_technology = data_technology.loc[(data_technology['medea_type'] < 60) | (data_technology['medea_type'] >= 70), :]

data_hydstores = pd.read_excel(os.path.join(cfg.folder, 'medea', 'data', 'processed', 'plant-list_hydro.xlsx'),
                               'opsd_hydro')
data_atc = pd.read_excel(os.path.join(cfg.folder, 'medea', 'data', 'processed', 'data_static.xlsx'),
                         'NTC', index_col=[0])
data_atc = data_atc.loc[data_atc.index.str.contains('|'.join(cfg.zones)),
                        data_atc.columns.str.contains('|'.join(cfg.zones))] / 1000

# --------------------------------------------------------------------------- #
# %% preprocessing plant data
# --------------------------------------------------------------------------- #
# select active thermal plants
data_plant = pd.read_excel(os.path.join(cfg.folder, 'medea', 'data', 'processed', 'power_plant_db.xlsx'))
data_plant_active = data_plant[(data_plant['UnitOperOnlineDate'] < pd.Timestamp(cfg.year, 1, 1)) &
                               ((data_plant['UnitOperRetireDate'] > pd.Timestamp(cfg.year, 12, 31)) | np.isnat(
                                 data_plant['UnitOperRetireDate']))]
data_plant_active = data_plant_active[(data_plant_active.MedeaType < 60) | (data_plant_active.MedeaType >= 70)]

# distinguish between plants in different countries
tec_props = data_plant_active.groupby(['MedeaType', 'PlantCountry'])['UnitNameplate'].sum().to_frame() / 1000
tec_props['eta'] = data_plant_active.groupby(['MedeaType', 'PlantCountry'])['Eta'].mean().to_frame()
tec_props['count'] = data_plant_active.groupby(['MedeaType'])['PlantCountry'].value_counts().to_frame(name='count')
tec_props['num'] = (tec_props['UnitNameplate'].round(decimals=1)*10).astype(int)
tec_props.rename(index={'Germany': 'DE', 'Austria': 'AT'}, columns={'UnitNameplate': 'cap'}, inplace=True)
tec_props = tec_props.unstack(-1)
tec_props.drop(0.0, axis=0, inplace=True)
# add data for heat boilers
dict_boil_props = {('cap', 'AT'): 4.5, ('cap', 'DE'): 25.5, ('eta', 'AT'): 0.9, ('eta', 'DE'): 0.9,
                   ('count', 'AT'): 15, ('count', 'DE'): 85, ('num', 'AT'): 85, ('num', 'DE'): 255}
tec_props = tec_props.append(pd.DataFrame(data=dict_boil_props.values(), index=dict_boil_props.keys(),
                                          columns=[49.5]).T)
# add data for heatpumps
dict_htpump_props = {('cap', 'AT'): 0.1, ('cap', 'DE'): 0.1, ('eta', 'AT'): 3.0, ('eta', 'DE'): 3.0,
                     ('count', 'AT'): 1, ('count', 'DE'): 1, ('num', 'AT'): 1, ('num', 'DE'): 1}
tec_props = tec_props.append(pd.DataFrame(data=dict_htpump_props.values(), index=dict_htpump_props.keys(),
                                          columns=[100.0]).T)

# TODO: Throws SettingWithCopyWarning: A value is trying to be set on a copy of a slice from a DataFrame
for zone in cfg.zones:
    tec_props.loc[:, 'eta'].update(pd.DataFrame.from_dict(efficiency_electric, orient='index', columns=[zone]),
                                   overwrite=False)

# set index of tec_props to plant names
df_map = (data_technology.loc[data_technology['medea_type'].isin(tec_props.index),
                              'medea_type']).reset_index().set_index('medea_type')
tec_props.index = df_map.loc[tec_props.index, 'set_element']
tec_props = tec_props.copy()
tec_props = tec_props.stack(-1).swaplevel(axis=0)
tec_props = tec_props.dropna()

df_feasops = data_feasops.copy()
df_feasops['fuel_name'] = (df_feasops['medea_type']/10).apply(np.floor)*10
df_feasops['medea_type'] = df_map.loc[df_feasops['medea_type'], 'set_element'].values
df_feasops['fuel_name'] = df_feasops['fuel_name'].replace({y: x for x, y in fuel_set.items()})
df_feasops.dropna(inplace=True)
df_feasops.set_index(['medea_type', 'l', 'fuel_name'], inplace=True)
df_eff = df_efficiency.droplevel('product').stack().reorder_levels([0, 2, 1])
# following line produces memory error (0xC00000FD) --> workaround with element-wise division
# df_feasops['fuel_need'] = df_feasops['fuel']/ df_eff
df_feasops['fuel_need'] = np.nan
for typ in df_feasops.index.get_level_values(0).unique():
    for lim in df_feasops.index.get_level_values(1).unique():
        df_feasops.loc[idx[typ, lim], 'fuel_need'] = df_feasops.loc[idx[typ, lim], 'fuel'].mean() / df_eff.loc[idx[typ, lim], :].mean()
# if unit commit model: consider adjustment to account for model being in GW while plant size is in steps of 100 MW
# df_feasops = df_feasops / 10

# hydro storage data
# hydro storages
hyd_store_data = pd.read_excel(os.path.join(cfg.folder, 'medea', 'data', 'processed', 'plant-list_hydro.xlsx'),
                               'opsd_hydro')
# drop all ror data
hyd_store_data.drop(hyd_store_data[hyd_store_data.technology == 'Run-of-river'].index, inplace=True)
# filter out data without reservoir size in GWh
hyd_store_data.dropna(subset=['energy_max', 'power_in'], inplace=True)
# calculate duration of generation from full reservoir
hyd_store_data['max_duration'] = hyd_store_data['energy_max'] / hyd_store_data['power_out'] * 1000 / 24
hyd_store_data['count'] = 1
hyd_store_clusters = hyd_store_data.groupby(['technology', 'country', pd.cut(hyd_store_data['max_duration'],
                                                                           [0, 2, 7, 75])]).sum()
hyd_store_clusters['efficiency_in'] = hyd_store_clusters['efficiency_in'] / hyd_store_clusters['count']
hyd_store_clusters['efficiency_out'] = hyd_store_clusters['efficiency_out'] / hyd_store_clusters['count']
hyd_store_clusters['cost_power'] = np.nan
hyd_store_clusters['cost_energy'] = np.nan
# assign technology and zone index to rows
hyd_store_clusters['country'] = hyd_store_clusters.index.get_level_values(1)
hyd_store_clusters['category'] = hyd_store_clusters.index.get_level_values(2).rename_categories(
    ['day', 'week', 'season']).astype(str)
hyd_store_clusters['tech'] = hyd_store_clusters.index.get_level_values(0)
hyd_store_clusters['tech'] = hyd_store_clusters['tech'].replace(['Pumped Storage', 'Reservoir'], ['psp', 'res'])
hyd_store_clusters['set_elem'] = hyd_store_clusters['tech'] + '_' + hyd_store_clusters['category']
hyd_store_clusters = hyd_store_clusters.set_index(['set_elem', 'country'])
hyd_store_clusters.fillna(0, inplace=True)
hyd_store_clusters['power_out'] = hyd_store_clusters['power_out'] / 1000  # conversion from MW to GW
hyd_store_clusters['power_in'] = hyd_store_clusters['power_in'] / 1000  # conversion from MW to GW
hyd_store_clusters['inflow_factor'] = (hyd_store_clusters['energy_max'] / hyd_store_clusters['energy_max'].sum())
del hyd_store_data


storage_clusters = hyd_store_clusters.loc[:, ['power_in', 'power_out', 'energy_max', 'efficiency_in', 'efficiency_out',
                                              'cost_power', 'cost_energy', 'inflow_factor']].copy()
# append battery data
df_inv_storage = pd.read_excel(os.path.join(cfg.folder, 'medea', 'data', 'processed', 'data_static.xlsx'),
                               'invest_storage', header=[0, 1], index_col=[0])

dict_battery = {
    'power_in': [0],
    'power_out': [0],
    'energy_max': [0],
    'efficiency_in': [0.96],
    'efficiency_out': [0.96],
    'cost_power': [df_inv_storage.loc['battery', ('annuity-power', 'AT')].round(4)],
    'cost_energy': [df_inv_storage.loc['battery', ('annuity-energy', 'AT')].round(4)],
    'inflow_factor': [0]
}
bat_idx = pd.MultiIndex.from_product([['battery'], list(cfg.zones)])
df_battery = pd.DataFrame(np.nan, bat_idx, dict_battery.keys())
for zone in list(cfg.zones):
    for key in dict_battery.keys():
        df_battery.loc[('battery', zone), key] = dict_battery[key][0]

storage_clusters = storage_clusters.append(df_battery)

# --------------------------------------------------------------------------- #
# %% process time series data
# --------------------------------------------------------------------------- #
ts_medea = pd.read_csv(os.path.join(cfg.folder, 'medea', 'data', 'processed', 'medea_regional_timeseries.csv'))
ts_medea['DateTime'] = pd.to_datetime(ts_medea['DateTime'])
ts_medea.set_index('DateTime', inplace=True)
# constrain data to scenario year
ts_medea = ts_medea.loc[(pd.Timestamp(cfg.year, 1, 1, 0, 0).tz_localize('UTC') <= ts_medea.index) & (
        ts_medea.index <= pd.Timestamp(cfg.year, 12, 31, 23, 0).tz_localize('UTC'))]
# drop index and set index of df_time instead
if len(ts_medea) == len(df_time):
    ts_medea.set_index(df_time.index, inplace=True)
else:
    raise ValueError('Mismatch of time series data and model time resolution. Is cfg.year wrong?')
ts_medea['DE-power-load'] = ts_medea['DE-power-load'] / 0.91
# for 0.91 scaling factor see
# https://www.entsoe.eu/fileadmin/user_upload/_library/publications/ce/Load_and_Consumption_Data.pdf

# subset of zonal time series
ts_zonal = ts_medea.loc[:, ts_medea.columns.str.startswith(('AT', 'DE'))].copy()
ts_zonal.columns = ts_zonal.columns.str.split('-', expand=True)
# adjust column naming to reflect proper product names ('el' and 'ht')
ts_zonal = ts_zonal.rename(columns={'power': 'el', 'heat': 'ht'})

# create price time series incl transport cost
ts_medea['Nuclear'] = 3.5
ts_medea['Lignite'] = 4.5
ts_medea['Biomass'] = 6.5

model_prices = ['Coal', 'Oil', 'Gas', 'EUA', 'Nuclear', 'Lignite', 'Biomass', 'price_day_ahead']

data_cost_transport = pd.read_excel(os.path.join(cfg.folder, 'medea', 'data', 'processed', 'data_static.xlsx'),
                                    'cost_transport', header=[0], index_col=[0])
ts_price = pd.DataFrame(index=ts_medea.index, columns=pd.MultiIndex.from_product([model_prices, cfg.zones]))
for zone in cfg.zones:
    for fuel in model_prices:
        if fuel in data_cost_transport.index:
            ts_price[(fuel, zone)] = ts_medea[fuel] + data_cost_transport.loc[fuel, zone]
        else:
            ts_price[(fuel, zone)] = ts_medea[fuel]


ts_inflows = pd.DataFrame(index=list(ts_zonal.index), columns=pd.MultiIndex.from_product([cfg.zones, df_tec_strg.index]))
for zone in list(cfg.zones):
    for strg in df_tec_strg.index:
        if 'battery' not in strg:
            ts_inflows.loc[:, (zone, strg)] = ts_zonal.loc[:, idx[zone, 'inflows', 'reservoir']] * \
                                              storage_clusters.loc[(strg, zone), 'inflow_factor']

df_ancil = ts_zonal.loc[:, idx[:, 'el', 'load']].max().unstack((1, 2)).squeeze() * 0.125 + \
           df_itm_cap.unstack(1).drop('ror', axis=1).sum(axis=1) * 0.075

# --------------------------------------------------------------------------- #
# %% limits on investment - long-run vs short-run & # TODO: potentials
# --------------------------------------------------------------------------- #
invest_potentials = pd.read_excel(os.path.join(cfg.folder, 'medea', 'data', 'processed', 'data_static.xlsx'),
                                  'potentials', header=[0], index_col=[0])
lim_invest_thermal = pd.DataFrame([0])
if cfg.invest_conventionals:
    lim_invest_thermal = pd.DataFrame([float('inf')])

# dimension lim_invest_itm[r, tec_itm]
lim_invest_itm = pd.DataFrame(data=0, index=cfg.zones, columns=df_tec_itm.index)
if cfg.invest_renewables:
    for zone in cfg.zones:
        for itm in lim_invest_itm.columns:
            lim_invest_itm.loc[zone, itm] = float(invest_potentials.loc[itm, zone])

# dimension lim_invest_storage[r, tec_strg]
lim_invest_storage = pd.DataFrame(data=0, index=cfg.zones, columns=df_tec_strg.index)
if cfg.invest_storage:
    for zone in cfg.zones:
        for strg in lim_invest_storage.columns:
            lim_invest_storage.loc[zone, strg] = float(invest_potentials.loc[strg, zone])

# dimension lim_invest_atc[r,rr]
lim_invest_atc = pd.DataFrame(data=0, index=cfg.zones, columns=cfg.zones)
if cfg.invest_tc:
    for zone in cfg.zones:
        lim_invest_atc.loc[zone, lim_invest_atc.index.difference([zone])] = float('inf')
