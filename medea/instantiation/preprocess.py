import os

import numpy as np
import pandas as pd

import config as cfg
from medea.helper_functions import is_leapyear

# --------------------------------------------------------------------------- #
# %% settings and initializing
# --------------------------------------------------------------------------- #
idx = pd.IndexSlice
bool_invest_itm = pd.DataFrame([0])
bool_invest_thermal = pd.DataFrame([0])
if cfg.invest_renewables:
    bool_invest_itm = pd.DataFrame([float('inf')])
if cfg.invest_conventionals:
    bool_invest_thermal = pd.DataFrame([float('inf')])

# --------------------------------------------------------------------------- #
# %% prepare set data
# --------------------------------------------------------------------------- #
fuel_set = {'Nuclear': 10, 'Lignite': 20, 'Coal': 30, 'Gas': 40, 'Oil': 50, 'Hydro': 60,
            'Biomass': 70, 'Solar': 80, 'Wind': 90, 'Power': 100, 'Heat': 110}
df_fuel = pd.DataFrame(fuel_set.values(), fuel_set.keys(), ['Value'])
df_lim = pd.DataFrame(data=True, index=[f'l{x}' for x in range(1, 6)], columns=['Value'])
df_prd = pd.DataFrame(data=True, index=['power', 'heat'], columns=['Value'])
df_props = pd.DataFrame(data=True,
                        index=['cap_turbine', 'cap_pump', 'cap_reservoir', 'efficiency_turbine', 'efficiency_pump'],
                        columns=['Value'])
df_regions = pd.DataFrame(data=True, index=cfg.regions, columns=['Value'])
df_tec_itm = pd.DataFrame(data=True, index=['pv', 'ror', 'wind_on', 'wind_off'], columns=['Value'])
df_tec_hsp = pd.DataFrame(data=True, index=['psp_day', 'psp_week', 'psp_season', 'res_day', 'res_week', 'res_season'],
                          columns=['Value'])
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
df_efficiency['product'] = 'power'
df_efficiency.loc[df_efficiency.index.str.contains('pth'), 'product'] = 'heat'
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
data_itm_cap = pd.read_excel(os.path.join(cfg.folder, 'data', 'processed', 'plant_props.xlsx'), 'itm_installed',
                             header=[0, 1], index_col=[0])
df_itm_cap = data_itm_cap.loc[cfg.year, :]

data_itm_invest = pd.read_excel(os.path.join(cfg.folder, 'data', 'processed', 'plant_props.xlsx'), 'itm_invest',
                                index_col=[0])
df_itm_invest = data_itm_invest.loc[:, [f'annuity-{r}' for r in cfg.regions]]
df_itm_invest.columns = pd.MultiIndex.from_product([['annuity'], cfg.regions])

data_technology = pd.read_excel(os.path.join(cfg.folder, 'data', 'processed', 'plant_props.xlsx'), 'flex_params')

data_feasops = pd.read_excel(os.path.join(cfg.folder, 'data', 'processed', 'Plant_props.xlsx'), 'gen_possibilities')

data_technology.set_index('set_element', inplace=True)
data_technology = data_technology.loc[(data_technology['medea_type'] < 60) | (data_technology['medea_type'] >= 70), :]

data_hydstores = pd.read_excel(os.path.join(cfg.folder, 'data', 'processed', 'plant-list_hydro.xlsx'), 'opsd_hydro')
data_ntc = pd.read_excel(os.path.join(cfg.folder, 'data', 'processed', 'plant_props.xlsx'), 'NTC', index_col=[0])
data_ntc = data_ntc.loc[data_ntc.index.str.contains('|'.join(cfg.regions)),
                        data_ntc.columns.str.contains('|'.join(cfg.regions))] / 1000

# --------------------------------------------------------------------------- #
# %% preprocessing plant data
# --------------------------------------------------------------------------- #
# select active thermal plants
data_plant = pd.read_excel(os.path.join(cfg.folder, 'data', 'processed', 'power_plant_db.xlsx'))
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

for reg in cfg.regions:
    tec_props.loc[:, 'eta'].update(pd.DataFrame.from_dict(efficiency_electric, orient='index', columns=[reg]),
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
df_feasops['fuel_name'] = df_feasops['fuel_name'].replace({y: x for x, y in fuel_set.items()})
df_feasops['medea_type'] = df_map.loc[df_feasops['medea_type'], 'set_element'].values
df_feasops.dropna(inplace=True)
df_feasops.set_index(['medea_type', 'l', 'fuel_name'], inplace=True)
df_eff = df_efficiency.droplevel('product').stack().reorder_levels([0, 2, 1])
# following line produces memory error (0xC00000FD) --> workaround with element-wise division
# df_feasops['fuel_need'] = df_feasops['fuel']/ df_eff
df_feasops['fuel_need'] = np.nan
for typ in df_feasops.index.get_level_values(0).unique():
    for lim in df_feasops.index.get_level_values(1).unique():
        df_feasops.loc[(typ, lim), 'fuel_need'] = df_feasops.loc[(typ, lim), 'fuel'].values / df_eff.loc[
            (typ, lim)].values
# adjustment to account for model being in GW while plant size is in steps of 100 MW
df_feasops = df_feasops / 10

# hydro storage data
# hydro storages
hyd_store_data = pd.read_excel(os.path.join(cfg.folder, 'data', 'processed', 'plant-list_hydro.xlsx'), 'opsd_hydro')
# drop all ror data
hyd_store_data.drop(hyd_store_data[hyd_store_data.technology == 'Run-of-river'].index, inplace=True)
# filter out data without reservoir size in GWh
hyd_store_data.dropna(subset=['cap_reservoir', 'cap_pump'], inplace=True)
# calculate duration of generation from full reservoir
hyd_store_data['max_duration'] = hyd_store_data['cap_reservoir'] / hyd_store_data['cap_turbine'] * 1000 / 24
hyd_store_data['count'] = 1
hyd_store_clusters = hyd_store_data.groupby(['technology', 'country', pd.cut(hyd_store_data['max_duration'],
                                                                             [0, 2, 7, 75])]).sum()
hyd_store_clusters['efficiency_pump'] = hyd_store_clusters['efficiency_pump'] / hyd_store_clusters['count']
hyd_store_clusters['efficiency_turbine'] = hyd_store_clusters['efficiency_turbine'] / hyd_store_clusters['count']
# assign technology and region index to rows
hyd_store_clusters['country'] = hyd_store_clusters.index.get_level_values(1)
hyd_store_clusters['category'] = hyd_store_clusters.index.get_level_values(2).rename_categories(
    ['day', 'week', 'season']).astype(str)
hyd_store_clusters['tech'] = hyd_store_clusters.index.get_level_values(0)
hyd_store_clusters['tech'] = hyd_store_clusters['tech'].replace(['Pumped Storage', 'Reservoir'], ['psp', 'res'])
hyd_store_clusters['set_elem'] = hyd_store_clusters['tech'] + '_' + hyd_store_clusters['category']
hyd_store_clusters = hyd_store_clusters.set_index(['set_elem', 'country'])
hyd_store_clusters.fillna(0, inplace=True)
hyd_store_clusters['cap_turbine'] = hyd_store_clusters['cap_turbine'] / 1000  # conversion from MW to GW
hyd_store_clusters['cap_pump'] = hyd_store_clusters['cap_pump'] / 1000  # conversion from MW to GW
hyd_store_clusters['inflow_factor'] = (hyd_store_clusters['cap_reservoir'] / hyd_store_clusters['cap_reservoir'].sum())
del hyd_store_data

# --------------------------------------------------------------------------- #
# %% process time series data
# --------------------------------------------------------------------------- #
ts_medea = pd.read_csv(os.path.join(cfg.folder, 'data', 'processed', 'medea_regional_timeseries.csv'))
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

# subset of regional time series
ts_regional = ts_medea.loc[:, ts_medea.columns.str.startswith(('AT', 'DE'))].copy()
ts_regional.columns = ts_regional.columns.str.split('-', expand=True)

# create price time series
ts_price = ts_medea[['EUA', 'Gas', 'Coal', 'Oil', 'price_day_ahead']].copy()
ts_price['Nuclear'] = 3.5
ts_price['Lignite'] = 5.5
ts_price['Biomass'] = 7.5

ts_inflows = pd.DataFrame(index=list(ts_regional.index), columns=pd.MultiIndex.from_product([cfg.regions, df_tec_hsp.index]))
for reg in list(cfg.regions):
    for hsp in df_tec_hsp.index:
        ts_inflows.loc[:, (reg, hsp)] = ts_regional.loc[:, idx[reg, 'inflows', 'reservoir']] * \
                                        hyd_store_clusters.loc[(hsp, reg), 'inflow_factor']


df_ancil = ts_regional.loc[:, idx[:, 'power', 'load']].max().unstack((1, 2)).squeeze() * 0.125 + \
           df_itm_cap.unstack(1).drop('ror', axis=1).sum(axis=1) * 0.075

# TODO: LEGACY CODE -- reactivate?
"""
# --------------------------------------------------------------------------- #
#%% process time series data
# --------------------------------------------------------------------------- #
# generate availability time series
ts_outage = pd.read_csv(os.path.join(cfg.folder, 'data', 'outages_integer.csv'))
ts_outage.fillna(0, inplace=True)
ts_outage['DateTime'] = pd.to_datetime(ts_outage['DateTime'])
ts_outage.set_index('DateTime', drop=True, inplace=True)
dim = ts_outage.shape
# ts_n = pd.DataFrame(data=np.tile(cluster_data['count'], (dim[0], 1)), index=ts_outage['DateTime'],
#                    columns=cluster_data.index)
ts_avail = pd.DataFrame(data=np.tile(technology_set['count'], (dim[0], 1)), index=ts_outage.index,
                        columns=technology_set.index) - ts_outage
"""
