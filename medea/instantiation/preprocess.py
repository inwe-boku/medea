import os
import numpy as np
import pandas as pd
import config as cfg


# --------------------------------------------------------------------------- #
#%% prepare set data
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
df_time = pd.DataFrame({f't{hour}': True for hour in range(1, 8761)}.values(),
                       index={f't{hour}': True for hour in range(1, 8761)}.keys(), columns=['Value'])

# --------------------------------------------------------------------------- #
#%% prepare static data
# --------------------------------------------------------------------------- #
emission_intensity = {'Nuclear': 0, 'Lignite': 0.45, 'Coal': 0.333, 'Gas': 0.199, 'Oil': 0.275, 'Hydro': 0,
                      'Biomass': 0, 'Solar': 0, 'Wind': 0, 'Power': 0, 'Heat': 0}
df_emission_intensity = pd.DataFrame(emission_intensity.values(), emission_intensity.keys(), columns=['Value'])


# --------------------------------------------------------------------------- #
#%% data inputs
# --------------------------------------------------------------------------- #

data_itm_cap = pd.read_excel(os.path.join(cfg.folder, 'data', 'processed', 'plant_props.xlsx'), 'itm_installed', header=[0, 1], index_col=[0])
data_itm_invest = pd.read_excel(os.path.join(cfg.folder, 'data', 'processed', 'plant_props.xlsx'), 'itm_invest', index_col=[0])

data_technology = pd.read_excel(os.path.join(cfg.folder, 'data', 'processed', 'plant_props.xlsx'), 'flex_params')
data_technology.set_index('set_element', inplace=True)

data_feasops = pd.read_excel(os.path.join(cfg.folder, 'data', 'processed', 'Plant_props.xlsx'), 'gen_possibilities')
data_hydstores = pd.read_excel(os.path.join(cfg.folder, 'data', 'processed', 'plant-list_hydro.xlsx'), 'opsd_hydro')
data_ntc = pd.read_excel(os.path.join(cfg.folder, 'data', 'processed', 'plant_props.xlsx'), 'NTC', index_col=[0])


df_itm_cap = data_itm_cap.loc[cfg.year, :]
df_itm_invest = data_itm_invest.loc[:, 'annuity']
df_feasops = pd.merge(data_feasops, data_technology[['medea_type', 'set_element']], left_on='medea_type',
                      right_on='medea_type').set_index(['set_element', 'l'])
#TODO: factor in efficiencies
df_feasops = pd.melt(df_feasops[['set_element', 'l', 'power_prp', 'heat_prp']], id_vars=['set_element', 'l'],
                     value_vars=['power_prp', 'heat_prp'])

# --------------------------------------------------------------------------- #
#%% preprocessing plant data
# -------------------------------------------------------------------------
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
tec_props = tec_props.append(pd.DataFrame(data=dict_boil_props.values(), index=dict_boil_props.keys(), columns=[49.5]).T)
# set index of tec_props to plant names
df_map = (data_technology.loc[data_technology['medea_type'].isin(tec_props.index), 'medea_type']).reset_index().set_index('medea_type')
tec_props.index = df_map.loc[tec_props.index, 'set_element']
tec_props = tec_props.copy()

# update nan efficiency values
eff_fill = {'nuc': 0.34, 'lig_stm': 0.33, 'lig_stm_chp': 0.33, 'lig_boa': 0.43, 'lig_boa_chp': 0.43, 'coal_sub': 0.35,
       'coal_sub_chp': 0.35, 'coal_sc': 0.40, 'coal_sc_chp': 0.40, 'coal_usc': 0.44, 'coal_usc_chp': 0.44,
       'coal_igcc': 0.40, 'ng_stm': 0.40, 'ng_stm_chp': 0.40, 'ng_cbt_lo': 0.33, 'ng_cbt_lo_chp': 0.33,
       'ng_cbt_hi': 0.40, 'ng_cbt_hi_chp': 0.40, 'ng_cc_lo': 0.38, 'ng_cc_lo_chp': 0.38, 'ng_cc_hi': 0.55,
       'ng_cc_hi_chp': 0.55, 'ng_mtr': 0.40, 'ng_mtr_chp': 0.40, 'ng_boiler_chp': 0.90, 'ng_boiler': 0.90,
       'oil_stm': 0.31, 'oil_stm_chp': 0.31, 'oil_cbt': 0.35, 'oil_cbt_chp': 0.35, 'oil_cc': 0.42,
       'oil_cc_chp': 0.42, 'hyd_ror': 0.98, 'hyd_res': 0.94, 'hyd_psp': 0.8, 'bio': 0.35, 'bio_chp': 0.35}
for reg in cfg.regions:
    tec_props.loc[:, 'eta'].update(pd.DataFrame.from_dict(eff_fill, orient='index', columns=[reg]), overwrite=False)




# --------------------------------------------------------------------------- #
#%% legacy code
# --------------------------------------------------------------------------- #


eff_guess = {'nuc': 0.34, 'lig_stm': 0.33, 'lig_stm_chp': 0.33, 'lig_boa': 0.43, 'lig_boa_chp': 0.43, 'coal_sub': 0.35,
       'coal_sub_chp': 0.35, 'coal_sc': 0.40, 'coal_sc_chp': 0.40, 'coal_usc': 0.44, 'coal_usc_chp': 0.44,
       'coal_igcc': 0.40, 'ng_stm': 0.40, 'ng_stm_chp': 0.40, 'ng_cbt_lo': 0.33, 'ng_cbt_lo_chp': 0.33,
       'ng_cbt_hi': 0.40, 'ng_cbt_hi_chp': 0.40, 'ng_cc_lo': 0.38, 'ng_cc_lo_chp': 0.38, 'ng_cc_hi': 0.55,
       'ng_cc_hi_chp': 0.55, 'ng_mtr': 0.40, 'ng_mtr_chp': 0.40, 'ng_boiler_chp': 0.90, 'ng_boiler': 0.90,
       'oil_stm': 0.31, 'oil_stm_chp': 0.31, 'oil_cbt': 0.35, 'oil_cbt_chp': 0.35, 'oil_cc': 0.42,
       'oil_cc_chp': 0.42, 'hyd_ror': 0.98, 'hyd_res': 0.94, 'hyd_psp': 0.8, 'bio': 0.35, 'bio_chp': 0.35}


fuel_set_inv = {y: x for x, y in fuel_set.items()}



time_range = pd.date_range(pd.datetime(cfg.year, 1, 1, 0, 0, 0), end=pd.datetime(cfg.year, 12, 31, 23, 0, 0), freq='H')
time_set = pd.DataFrame(index=time_range, columns=['time_elements'])
for hr, val in enumerate(time_range):
    time_set['time_elements'].loc[time_range[hr]] = f't{hr + 1}'
del val, time_range

df_time_set = pd.DataFrame({f't{hour}': True for hour in range(1, 8761)}.values(),
                  index={f't{hour}': True for hour in range(1, 8761)}.keys())

technology_set = pd.read_excel(os.path.join(cfg.folder, 'data', 'processed', 'plant_props.xlsx'), 'flex_params')
hydro_storage_set = ['psp_day', 'psp_week', 'psp_season', 'res_day', 'res_week', 'res_season']
intermittent_set = ['pv', 'ror', 'wind_on', 'wind_off']

# --------------------------------------------------------------------------- #
#%% prepare static data
# --------------------------------------------------------------------------- #

specific_emissions = {'Nuclear': 0, 'Lignite': 0.45, 'Coal': 0.333, 'Gas': 0.199, 'Oil': 0.275, 'Hydro': 0,
                      'Biomass': 0, 'Solar': 0, 'Wind': 0, 'Power': 0, 'Heat': 0}

# --------------------------------------------------------------------------- #
# prepare technology data
plant_db = pd.read_excel(os.path.join(cfg.folder, 'data', 'processed', 'power_plant_db.xlsx'))
# filter/remove power plants that are not active in the chosen year
active_plants = plant_db[(plant_db['UnitOperOnlineDate'] < pd.Timestamp(cfg.year, 1, 1)) &
                         ((plant_db['UnitOperRetireDate'] > pd.Timestamp(cfg.year, 12, 31)) | np.isnat(
                             plant_db['UnitOperRetireDate']))]
del plant_db
# exclude hydro plants
active_plants = active_plants[(active_plants.MedeaType < 60) | (active_plants.MedeaType >= 70)]
# distinguish between plants in AT and DE
tec_props = active_plants.groupby(['MedeaType', 'PlantCountry'])['UnitNameplate'].sum().to_frame() / 1000
tec_props['eta'] = active_plants.groupby(['MedeaType', 'PlantCountry'])['Eta'].mean().to_frame()
num = active_plants.groupby(['MedeaType', 'PlantCountry'])['MedeaType'].value_counts().to_frame(name='count')
num.index = num.index.droplevel(-1)
tec_props = pd.merge(tec_props, num, left_index=True, right_index=True)

del active_plants, num
idx = pd.IndexSlice
tec_props_AT = tec_props.loc[idx[:, 'Austria'], :]
tec_props_AT.index = tec_props_AT.index.droplevel(-1)
tec_props_AT.columns = ['cap_AT', 'eta_AT', 'count_AT']
tec_props_AT = tec_props_AT.copy()  # why is this needed?
tec_props_AT.loc[:, 'num_AT'] = (tec_props_AT.loc[:, 'cap_AT'].round(decimals=1)*10).astype(int)
tec_props_DE = tec_props.loc[idx[:, 'Germany'], :]
tec_props_DE.index = tec_props_DE.index.droplevel(-1)
tec_props_DE.columns = ['cap_DE', 'eta_DE', 'count_DE']
tec_props_DE = tec_props_DE.copy()  # why?
tec_props_DE['num_DE'] = (tec_props_DE['cap_DE'].round(decimals=1)*10).astype(int)
del tec_props
# bind capacities and efficiencies to cluster data frame
technology_set = pd.merge(technology_set, tec_props_AT, how='left', left_on='medea_type', right_index=True)
technology_set = pd.merge(technology_set, tec_props_DE, how='left', left_on='medea_type', right_index=True)
# add hot water boilers
technology_set = technology_set.append(
    {'medea_type': 49.5, 'set_element': 'ng_boiler_chp', 'TD': 1, 'TU': 1, 'TSU_s1': 1, 'TSU_s2': 2, 'TSU_s3': 3,
     'CSU_s1': 1, 'CSU_s2': 1.1, 'CSU_s3': 1.2, 'CSD': 1, 'ramp': 0.99, 'om_var': 1.0, 'om_fix': 10.0, 'invest': 200,
     'cap_AT': 4.5, 'cap_DE': 25.5, 'eta_AT': 0.9, 'eta_DE': 0.9, 'count_AT': 15, 'count_DE': 85, 'num_AT': 85,
     'num_DE': 255}, ignore_index=True)
technology_set.sort_values(by=['medea_type'], inplace=True)
technology_set.set_index('set_element', inplace=True)
technology_set = technology_set.fillna(0)
for reg in region_set:
    df_effguess = pd.DataFrame().from_dict(eff_guess, orient='index', columns=[f'eta_{reg}'])
    technology_set.loc[technology_set[f'eta_{reg}']==0, f'eta_{reg}'] = df_effguess

# --------------------------------------------------------------------------- #
# generation possibilities for co-gen units
feas_op_region = pd.read_excel(os.path.join(cfg.folder, 'data', 'processed', 'Plant_props.xlsx'), 'gen_possibilities')

# translate medea-types to technology ids
medea_ids = pd.concat([technology_set.index.to_frame(), technology_set.medea_type], axis=1)

# merge and filter for existing plants
feas_op_region = pd.merge(feas_op_region, medea_ids, on='medea_type')
# if model is linear, adjust feasible operation regions to include zero-generation of power and heat
if cfg.model_type == 'linear':
    feas_op_region.loc[(feas_op_region['l'] == 'l1') & (feas_op_region['medea_type'] % 1 > 0), 'heat_prp'] = 0
    feas_op_region.loc[(feas_op_region['l'] == 'l3') & (feas_op_region['medea_type'] % 1 > 0), 'power_prp'] = 0
    feas_op_region.loc[(feas_op_region['l'] == 'l4') & (feas_op_region['medea_type'] % 1 > 0), 'power_prp'] = 0
    feas_op_region.loc[(feas_op_region['l'] == 'l4') & (feas_op_region['medea_type'] % 1 > 0), 'heat_prp'] = 0
    feas_op_region.loc[(feas_op_region['l'] == 'l4') & (feas_op_region['medea_type'] % 1 > 0), 'fuel_prp'] = 0

# --------------------------------------------------------------------------- #
# intermittent generation - installed capacities & investment costs
itm_cap = pd.read_excel(os.path.join(cfg.folder, 'data', 'processed', 'plant_props.xlsx'), 'itm_installed', header=[0, 1], index_col=[0])
itm_invest = pd.read_excel(os.path.join(cfg.folder, 'data', 'processed', 'plant_props.xlsx'), 'itm_invest', index_col=[0])

# --------------------------------------------------------------------------- #
# hydro storages
hyd_store_data = pd.read_excel(os.path.join(cfg.folder, 'data', 'processed', 'plant-list_hydro.xlsx'), 'opsd_hydro')
# drop all ror data
hyd_store_data.drop(hyd_store_data[hyd_store_data.technology == 'Run-of-river'].index, inplace=True)
# filter out data without reservoir size in GWh
hyd_store_data.dropna(subset=['cap_reservoir', 'cap_pump'], inplace=True)
# calculate duration of generation from full reservoir
hyd_store_data['max_duration'] = hyd_store_data['cap_reservoir'] / hyd_store_data['cap_turbine'] * 1000 / 24
hyd_store_data['count'] = 1
hyd_store_clusters = hyd_store_data.groupby(['technology', 'country', pd.cut(hyd_store_data['max_duration'], [0, 2, 7, 75])]).sum()
hyd_store_clusters['efficiency_pump'] = hyd_store_clusters['efficiency_pump'] / hyd_store_clusters['count']
hyd_store_clusters['efficiency_turbine'] = hyd_store_clusters['efficiency_turbine'] / hyd_store_clusters['count']
# assign technology and region index to rows
hyd_store_clusters['country'] = hyd_store_clusters.index.get_level_values(1)
hyd_store_clusters['category'] = hyd_store_clusters.index.get_level_values(2).rename_categories(['day', 'week', 'season']).astype(str)
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
# transmission capacities
ntc_data = pd.read_excel(os.path.join(cfg.folder, 'data', 'processed', 'plant_props.xlsx'), 'NTC', index_col=[0])
ntc_data = ntc_data / 1000

# --------------------------------------------------------------------------- #
#%% process time series data
# --------------------------------------------------------------------------- #
ts_medea = pd.read_csv(os.path.join(cfg.folder, 'data', 'processed', 'medea_regional_timeseries.csv'))
ts_medea['DateTime'] = pd.to_datetime(ts_medea['DateTime'])
ts_medea.set_index('DateTime', inplace=True)
ts_medea['DE_load_power'] = ts_medea['DE_load_power'] / 0.91
# for 0.91 scaling factor see
# https://www.entsoe.eu/fileadmin/user_upload/_library/publications/ce/Load_and_Consumption_Data.pdf
# constrain data to scenario year
ts_medea = ts_medea.loc[(pd.Timestamp(cfg.year, 1, 1, 0, 0).tz_localize('UTC') <= ts_medea.index) & (
        ts_medea.index <= pd.Timestamp(cfg.year, 12, 31, 23, 0).tz_localize('UTC'))]
# set prices for non-exchange traded fuels
ts_medea['Nuclear'] = 3.5
ts_medea['Lignite'] = 5.5
ts_medea['Biomass'] = 7.5

"""  REQUIRES REGIONALIZED VERSION
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
