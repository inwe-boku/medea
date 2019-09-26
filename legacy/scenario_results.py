# -*- coding: utf-8 -*-
"""
use medea to analyze Austrian energy and climate policy
@author: Sebastian Wehrle
"""

import os
import subprocess

import numpy as np
import pandas as pd
from gams import *

import config as cfg
from legacy.gams_wrappers import reset_parameter, gdx2df, df2gdx

# %% scenario assumptions
# Calibration of model (via efficiencies and capacities) to 2017 prices, fuel burn and emissions
baseline = {
    # [plant efficiencies] -------------- #
    'e_Nuclear': [1],
    'e_Biomass': [1],
    'e_Lignite': [1.15],
    'e_Coal': [1.225],
    'e_Gas': [1.15],
    'e_Oil': [1],
    # [capacity availability of plants ] ------ #
    'av_Nuclear': [0.72],
    'av_Lignite': [0.88],
    'av_Coal': [0.75],
    'av_Coal_chp': [0.775],
    'av_Gas': [0.9],
    'av_Gas_chp': [0.9],
    'av_Oil': [1.0],
    'av_Biomass': [0.8]
}
capcy = {
    'AT': {
        'bio': 0.8,
        'coal': 0.75,
        'lig': 0.8,
        'ng': 0.85,
        'nuc': 0.8,
        'oil': 0.85
    },
    'DE': {
        'bio': 0.8,
        'coal': 0.75,
        'lig': 0.88,
        'ng': 0.9,
        'nuc': 0.72,
        'oil': 0.9
    }
}

capcy_2030 = {
    'AT': {
        'bio': 0.8,
        'coal': 0,
        'lig': 0,
        'ng': 0.85,
        'nuc': 0.8,
        'oil': 0.85
    },
    'DE': {
        'bio': 0.85,
        'coal': 0.35,
        'lig': 0.45,
        'ng': 0.9,
        'nuc': 0.0,
        'oil': 0.9
    }
}

# Germany 2030: nuclear exit, coal phase out, renewables expansion as in EEG 2017
scenario_RES_DE2030 = {
    # nuclear phase-out in Germany
    # 'av_Nuclear': [0.0],
    # reduction of coal and lignite capacities in line with coal phase-out
    # 'av_Lignite': [0.45],
    # 'av_Coal': [0.35],
    # 'av_Coal_chp': [0.35],
    # 'av_Gas': [0.9],
    # 'av_Gas_chp': [1],
    # 'av_Oil': [0.8],
    # 'av_Biomass': [0.85],
    # expansion of res generation as laid out in German EEG 2017 by 2030: 90.8 GW onshore, 15 GW offshore, 73 GWp PV
    'c_wind_on': [90.8],  # [1.808],
    'c_wind_off': [15],  # [2.764],
    'c_pv': [73]  # [1.724]
}

# Austria 2030: additional electricity consumption due to electric mobility, heating, industry
scenario_AT2030 = {
    'd_Power': [1.18276362],
    'lim_wind_on': list(range(0, 16, 1))
}

# --------------------------------------------------------------------------- #
# %% initialize GAMS workspace and load model data
# --------------------------------------------------------------------------- #
ws = GamsWorkspace(system_directory=cfg.GMS_SYS_DIR)

db_input = ws.add_database_from_gdx(os.path.join(cfg.MEDEA_ROOT_DIR, 'medea', 'opt', 'medea_data.gdx'))
data_yr = db_input['year'].first_record().value

# read sets for clusters, hydro storage plants and products from db_input
clust_dict = {rec.keys[0] for rec in db_input['tec']}
chp_dict = {rec.keys[0] for rec in db_input['tec_chp']}
itm_dict = {rec.keys[0] for rec in db_input['tec_itm']}
hsp_dict = {rec.keys[0] for rec in db_input['props']}
prd_dict = {rec.keys[0] for rec in db_input['prd']}
fuel_dict = {rec.keys[0] for rec in db_input['f']}

# read parameters
df_eua = gdx2df(db_input, 'PRICE_EUA', ['t'], [])
# df_genprofile = gdx2df(db_input, 'GEN_PROFILE', ['r', 't', 'tec_itm'], [])
df_capitm = gdx2df(db_input, 'INSTALLED_CAP_ITM', ['r', 'tec_itm'], [])
# df_fuelprice = gdx2df(db_input, 'PRICE_FUEL', ['t', 'f'], [])
df_eff = gdx2df(db_input, 'EFFICIENCY', ['tec', 'prd', 'f'], [])
df_feasgen = gdx2df(db_input, 'FEASIBLE_OUTPUT', ['tec', 'l', 'prd'], [])
df_num = gdx2df(db_input, 'NUM', ['r', 'tec'], [])
df_fuelreq = gdx2df(db_input, 'FEASIBLE_INPUT', ['tec', 'l', 'f'], [])
# df_store_props = gdx2df(db_input, 'HSP_PROPERTIES', ['r', 'tec_hsp', 'props'], [])
# df_ancillary = gdx2df(db_input, 'ANCIL_SERVICE_LVL', ['r'], [])
df_load = gdx2df(db_input, 'CONSUMPTION', ['r', 't', 'prd'], [])

tec2fuel_map = gdx2df(db_input, 'EFFICIENCY', ['tec', 'f'], ['prd']).reset_index()
tec2fuel_map = tec2fuel_map.loc[tec2fuel_map['tec'].isin(df_feasgen.index.get_level_values(0)), :]

# --------------------------------------------------------------------------- #
# %% scenario generation
# --------------------------------------------------------------------------- #
idx = pd.IndexSlice
traded_fuels = ['Nuclear', 'Lignite', 'Gas', 'Oil', 'Coal', 'Biomass']

# write scenario-constant values to database:

# efficiency & availability / capacity
# efficiency
df_eff_mod = df_eff
for fl in traded_fuels:
    df_eff_mod.loc[idx[:, :, fl], :] = \
        df_eff.loc[idx[:, :, fl], :] * baseline[f'e_{fl}'][0]
reset_parameter(db_input, 'EFFICIENCY', df_eff_mod)
# feasible input of thermal plants
df_fuelreq_mod = df_fuelreq
for fl in traded_fuels:
    df_fuelreq_mod.loc[idx[:, :, fl], :] = \
        df_fuelreq.loc[idx[:, :, fl], :] / baseline[f'e_{fl}'][0]
reset_parameter(db_input, 'FEASIBLE_INPUT', df_fuelreq_mod)

# available capacity / number of plants
df_num_mod = df_num.copy()
for reg in cfg.zones:
    for fu in capcy[reg].keys():
        df_num_mod[df_num_mod.index.get_level_values(0).str.contains(reg) &
               (df_num_mod.index.get_level_values(1).str.contains(fu))] = \
            np.ceil(df_num[df_num.index.get_level_values(0).str.contains(reg) &
                           (df_num.index.get_level_values(1).str.contains(fu))] * capcy_2030[reg][fu])
reset_parameter(db_input, 'NUM', df_num_mod)
#                            (df_num.index.get_level_values(1).str.contains(fu))] * capcy[reg][fu])

# renewables expansion in Germany
df_capitm_mod = df_capitm
for itm in itm_dict:
    if itm != 'ror':
        df_capitm_mod.loc[idx['DE', itm], :] = scenario_RES_DE2030[f'c_{itm}'][0]
reset_parameter(db_input, 'INSTALLED_CAP_ITM', df_capitm_mod)
# df_capitm_mod.loc[idx['DE', itm], :] = df_capitm.loc[idx['DE', itm], :] * scenario_RES_DE2030[f'c_{itm}'][0]

# additional electricity consumption in Austria
df_load_mod = df_load
df_load_mod.loc[idx['AT', :, 'Power'], :] = df_load_mod.loc[idx['AT', :, 'Power'], :] * scenario_AT2030['d_Power'][0]
reset_parameter(db_input, 'CONSUMPTION', df_load_mod)

# allow for investment and disinvestment
reset_parameter(db_input, 'SWITCH_INVEST_THERM', pd.DataFrame([float('inf')], columns=['Value']))
reset_parameter(db_input, 'SWITCH_INVEST_ITM', pd.DataFrame([float('inf')]))


# %% iterate over changing values, i.e. over max wind_on capacity

# create wind_on-limit parameter
df_wonlim = pd.DataFrame(data=[0])
WONLIM = df2gdx(db_input, df_wonlim, 'WON_LIMIT', 'par', 0, 'upper limit on onshore wind capacity addition')
df_euafixed = pd.DataFrame(data=[0])
EUA_SCENARIO = df2gdx(db_input, df_euafixed, 'EUA_SCENARIO', 'par', 0, 'EUA price - scenario')

os.chdir(os.path.join(cfg.MEDEA_ROOT_DIR, 'medea', 'opt'))

for eua in range(50, 61, 10):
    reset_parameter(db_input, 'EUA_SCENARIO', pd.DataFrame(data=[eua]))
    for it in scenario_AT2030['lim_wind_on']:
        scenario_name = f'PoBu_EUA{eua}_curt_htpmp_{it}'
        # modify wind_on limit
        reset_parameter(db_input, 'WON_LIMIT', pd.DataFrame(data=[it]))
        # export gdx
        export_location = os.path.join(cfg.MEDEA_ROOT_DIR, 'medea', 'opt', f'MEDEA_{scenario_name}_data.gdx')
        db_input.export(export_location)
        # --------------------------------------------------------------------------- #
        # call GAMS
        gms_model = os.path.join(cfg.MEDEA_ROOT_DIR, 'medea', 'opt', 'medea_austria_htpmp.gms')
        gdx_out = f'gdx=medea_out_{scenario_name}.gdx'
        subprocess.run(f'{cfg.GMS_SYS_DIR}\\gams {gms_model} {gdx_out} lo=3 --scenario={scenario_name}')

    # delete input


"""
    # retrieve results
    read_variables = {'q_gen': (['t'], ['r', 'tec', 'prd']), 'q_fueluse': (['t'], ['r', 'tec', 'f']),
                      'res_level': (['t'], ['r', 'tec_hsp']), 'q_pump': (['t'], ['r', 'tec_hsp']),
                      'q_turbine': (['t'], ['r', 'tec_hsp']), 'q_curtail': (['t'], ['r', 'prd']),
                      'q_nonserved': (['t'], ['r', 'prd']), 'flow': (['t'], ['r', 'rr']),
                      'decommission': (['tec'], ['r']), 'invest_res': (['tec_itm'], ['r']),
                      'invest_thermal': (['tec'], ['r']), 'SD_balance_el': (['t'], ['r'])}

    gdx_solution_file = 'asdf'
    db_sol = ws.add_database_from_gdx(os.path.join(cfg.folder, 'medea', 'opt', gdx_out))
    obj_cost, result_dict = read_solution(db_sol, 'linear', read_variables)

    derived_dict = derived_solutions()

    for reg in regions:
        df_emis = df_emf['Value'] * burn_by_fuel.xs(reg, axis=1)
        df_emis.columns = pd.MultiIndex.from_product([[reg], df_emis.columns])
        emission_list.append(df_emis)
    co2_emissions = pd.concat(emission_list, axis=1).reindex(cols, level=1, axis=1)
    co2_total = co2_emissions.sum().sum()
"""
