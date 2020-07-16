# %% imports
import os
import numpy as np
import pandas as pd
import config as cfg

# --------------------------------------------------------------------------- #
# %% settings and initializing
# --------------------------------------------------------------------------- #
years = range(2012, 2020)
STATIC_FNAME = os.path.join(cfg.MEDEA_ROOT_DIR, 'data', 'processed', 'data_static.xlsx')
idx = pd.IndexSlice


# --------------------------------------------------------------------------- #
# %% functions
# --------------------------------------------------------------------------- #
# filter active thermal plants
def active_thermal_capacity(db_plant, year, dict_country, dict_id):
    active_plant = db_plant.loc[(db_plant['UnitOperOnlineDate'] < pd.Timestamp(year, 1, 1)) &
                                (db_plant['UnitOperRetireDate'] > pd.Timestamp(year, 12, 31)) |
                                np.isnat(db_plant['UnitOperRetireDate'])]
    active_plant = active_plant.loc[(active_plant['MedeaType'] < 60) | (active_plant['MedeaType'] >= 70)]
    aggregate_thermal_capacity = active_plant.groupby(['MedeaType',
                                                       'PlantCountry'])['UnitNameplate'].sum().to_frame() / 1000
    if dict_country:
        aggregate_thermal_capacity.rename(index=dict_country, columns={'UnitNameplate': 'cap'}, inplace=True)
    aggregate_thermal_capacity = aggregate_thermal_capacity.unstack(-1)
    aggregate_thermal_capacity.drop(0.0, axis=0, inplace=True)
    if dict_id:
        aggregate_thermal_capacity.rename(index=dict_id, inplace=True)
    return aggregate_thermal_capacity


# --------------------------------------------------------------------------- #
# %% input data
# --------------------------------------------------------------------------- #
plant_data = {
    'hydro': pd.read_excel(os.path.join(cfg.MEDEA_ROOT_DIR, 'data', 'processed', 'plant-list_hydro.xlsx'),
                           'opsd_hydro'),
    'conventional': pd.read_excel(os.path.join(cfg.MEDEA_ROOT_DIR, 'data', 'processed', 'power_plant_db.xlsx'))
}

countries_short = {'Germany': 'DE', 'Austria': 'AT'}

id_conversion = {
    10: 'nuc',
    20: 'lig_stm', 20.5: 'lig_stm_chp', 21: 'lig_boa', 21.5: 'lib_boa_chp',
    30: 'coal_sub', 30.5: 'coal_sub_chp', 31: 'coal_sc', 31.5: 'coal_sc_chp', 32: 'coal_usc',
    32.5: 'coal_usc_chp', 33: 'coal_igcc',
    40: 'ng_stm', 40.5: 'ng_stm_chp', 41: 'ng_cbt_lo', 41.5: 'ng_cbt_lo_chp', 42: 'ng_cbt_hi',
    42.5: 'ng_cbt_hi_chp', 43: 'ng_cc_lo', 43.5: 'ng_cc_lo_chp', 44: 'ng_cc_hi',
    44.5: 'ng_cc_hi_chp', 45: 'ng_mtr', 45.5: 'ng_mtr_chp', 49.5: 'ng_boiler',
    50: 'oil_stm', 50.5: 'oil_stm_chp', 51: 'oil_cbt', 51.5: 'oil_cbt_chp', 52: 'oil_cc',
    52.5: 'oil_cc_chp',
    60: 'ror', 61: 'res', 62: 'na', 63: 'psp',
    70: 'bio', 70.5: 'bio_chp',
    100: 'heatpump_pth', 101: 'hpa_pth', 102: 'eboi_pth'
}

# --------------------------------------------------------------------------- #
# %% thermal capacities
# --------------------------------------------------------------------------- #
cap_thermal = pd.DataFrame()
for y in years:
    df = active_thermal_capacity(plant_data['conventional'], y, countries_short, id_conversion)
    df.columns = df.columns.droplevel(0)
    df.columns = pd.MultiIndex.from_product([df.columns, [y]])
    cap_thermal = pd.concat([cap_thermal, df], axis=1, sort=False)

# --------------------------------------------------------------------------- #
# %% storage capacities
# --------------------------------------------------------------------------- #
# --------------------------------------------------------------------------- #
# hydro storages
plant_data['hydro'].drop(plant_data['hydro'][plant_data['hydro'].technology == 'Run-of-river'].index, inplace=True)
# filter out data without reservoir size in GWh
plant_data['hydro'].dropna(subset=['energy_max', 'power_in'], inplace=True)
# calculate duration of generation from fully filled reservoir
plant_data['hydro']['max_duration'] = plant_data['hydro']['energy_max'] / plant_data['hydro']['power_out'] * 1000 / 24
plant_data['hydro']['count'] = 1
plant_data.update({'hydro_clusters': plant_data['hydro'].groupby(
    ['technology', 'country', pd.cut(plant_data['hydro']['max_duration'], [0, 2, 7, 75])]).sum()})
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
# conversion from MW to GW
plant_data['hydro_clusters']['power_out'] = plant_data['hydro_clusters']['power_out'] / 1000
plant_data['hydro_clusters']['power_in'] = plant_data['hydro_clusters']['power_in'] / 1000
plant_data['hydro_clusters']['inflow_factor'] = (
        plant_data['hydro_clusters']['energy_max'] / plant_data['hydro_clusters']['energy_max'].sum())
plant_data['hydro_clusters'] = plant_data['hydro_clusters'].loc[:,
                               ['power_in', 'power_out', 'energy_max', 'inflow_factor']].copy()

# %% other storage capacity - batteries and hydrogen
# append battery data
bat_idx = pd.MultiIndex.from_product([['battery'], list(cfg.zones)])
df_battery = pd.DataFrame(np.nan, bat_idx, dict_additions['batteries'].keys())
for zone in list(cfg.zones):
    for key in dict_additions['batteries'].keys():
        df_battery.loc[('battery', zone), key] = dict_additions['batteries'][key][0]

plant_data['storage_clusters'] = plant_data['hydro_clusters'].append(df_battery)
