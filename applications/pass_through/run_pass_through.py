# -*- coding: utf-8 -*-
"""
use medea to estimate emission cost pass-through to electricity prices in the current and future electricity systems of Germany and Austria
@author: sweer
"""

import os
from shutil import copyfile

import pandas as pd
from gams import *

import config as cfg
from medea.gams_io import reset_parameter, gdx2df, df2gdx

# ---------------------------------------------------------------
# %% settings & scenario assumptions
project = 'pass_through'

# Calibration of model (via efficiencies and capacities) to 2017 prices, fuel burn and emissions
fuels = ['Nuclear', 'Lignite', 'Gas', 'Oil', 'Coal', 'Biomass']
techs = ['bio', 'coal', 'lig', 'ng', 'nuc', 'oil', 'wind_on', 'wind_off', 'pv']
efficiency = {
    # [plant efficiencies] -------------- #
    'e_Nuclear': [1],
    'e_Biomass': [1],
    'e_Lignite': [1.15],
    'e_Coal': [1.225],
    'e_Gas': [1.15],
    'e_Oil': [1]
}

capacity_scenario_name = ['cap_avail', 'cap_inst', 'cap_2030']

capacity_scenarios = {
    'AT': {
        'bio': [0.8, 1, 0.8],
        'coal': [0.75, 1, 0],
        'heatpump': [1, 1, 1],
        'lig': [0.8, 1, 0],
        'ng': [0.85, 1, 0.85],
        'nuc': [0, 0, 0],
        'oil': [0.85, 1, 0.85],
        'wind_on': [2, 2, 8],
        'wind_off': [0, 0, 0],
        'pv': [1, 1, 5]
    },
    'DE': {
        'bio': [0.8, 1, 0.85],
        'coal': [0.75, 1, 0.35],
        'heatpump': [1, 1, 1],
        'lig': [0.88, 1, 0.45],
        'ng': [0.9, 1, 0.9],
        'nuc': [0.72, 1, 0],
        'oil': [0.9, 1, 0.9],
        'wind_on': [50, 50, 90.8],
        'wind_off': [5, 5, 15],
        'pv': [50, 50, 73]
    }
}

euarange = range(5, 76, 5)


# --------------------------------------------------------------------------- #
# %% initialize GAMS, GAMS workspace and load model data
# --------------------------------------------------------------------------- #
# fetch main gams model, if required
if not os.path.isfile(os.path.join(cfg.folder, 'applications', project, 'opt', 'medea_main.gms')):
    copyfile(os.path.join(cfg.folder, 'medea', 'medea_main.gms'),
             os.path.join(cfg.folder, 'applications', project, 'opt', 'medea_main.gms'))
# fetch main gams data, if required
if not os.path.isfile(os.path.join(cfg.folder, 'applications', project, 'opt', 'medea_main_data.gdx')):
    copyfile(os.path.join(cfg.folder, 'medea', 'data', 'medea_main_data.gdx'),
             os.path.join(cfg.folder, 'applications', project, 'opt', 'medea_main_data.gdx'))

ws = GamsWorkspace(system_directory=cfg.gams_sysdir)

db_input = ws.add_database_from_gdx(os.path.join(cfg.folder, 'applications', project, 'opt', 'medea_main_data.gdx'))
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
df_capitm = gdx2df(db_input, 'INSTALLED_CAP_ITM', ['r', 'tec_itm'], [])
df_eff = gdx2df(db_input, 'EFFICIENCY', ['tec', 'prd', 'f'], [])
df_feasgen = gdx2df(db_input, 'FEASIBLE_OUTPUT', ['tec', 'l', 'prd'], [])
df_num = gdx2df(db_input, 'NUM', ['r', 'tec'], [])
df_fuelreq = gdx2df(db_input, 'FEASIBLE_INPUT', ['tec', 'l', 'f'], [])
tec2fuel_map = gdx2df(db_input, 'EFFICIENCY', ['tec', 'f'], ['prd']).reset_index()
tec2fuel_map = tec2fuel_map.loc[tec2fuel_map['tec'].isin(df_feasgen.index.get_level_values(0)), :]

# df_load = gdx2df(db_input, 'CONSUMPTION', ['r', 't', 'prd'], [])

# --------------------------------------------------------------------------- #
# %% scenario generation
# --------------------------------------------------------------------------- #
idx = pd.IndexSlice
# write scenario-constant values to database:

# efficiency
df_eff_mod = df_eff
for fl in fuels:
    df_eff_mod.loc[idx[:, :, fl], :] = \
        df_eff.loc[idx[:, :, fl], :] * efficiency[f'e_{fl}'][0]
reset_parameter(db_input, 'EFFICIENCY', df_eff_mod)
# feasible input of thermal plants
df_fuelreq_mod = df_fuelreq
for fl in fuels:
    df_fuelreq_mod.loc[idx[:, :, fl], :] = \
        df_fuelreq.loc[idx[:, :, fl], :] / efficiency[f'e_{fl}'][0]
reset_parameter(db_input, 'FEASIBLE_INPUT', df_fuelreq_mod)


# %% iterate over changing values, i.e. over eua prices and capacity scenarios
os.chdir(os.path.join(cfg.folder, 'applications', project, 'opt'))
EUA_SCENARIO = df2gdx(db_input, pd.DataFrame(data=[0]), 'EUA_SCENARIO', 'par', 0, 'EUA price - scenario')

for cap_scenario in range(0, 3, 1):   # capacity_scenarios:
    # conventional capacities
    df_num_mod = df_num
    for reg in cfg.regions:
        for gen in df_num.loc[reg].index:
            df_num_mod.loc[idx[reg, gen]] = (df_num.loc[idx[reg, gen]] *
                                             capacity_scenarios[reg][gen.split('_')[0]][cap_scenario]).round(0)

    reset_parameter(db_input, 'NUM', df_num_mod)

    # renewable capacities
    df_capitm_mod = df_capitm
    for reg in cfg.regions:
        for itm in itm_dict:
            if itm != 'ror':
                df_capitm_mod.loc[idx[reg, itm], :] = capacity_scenarios[reg][itm][cap_scenario]

    reset_parameter(db_input, 'INSTALLED_CAP_ITM', df_capitm_mod)

    # emission prices
    for peua in euarange:
        reset_parameter(db_input, 'EUA_SCENARIO', pd.DataFrame(data=[peua]))

        scenario = f'{capacity_scenario_name[cap_scenario]}_eua{peua}'
        # --------------------------------------------------------------------------- #
        # export gdx
        export_location = os.path.join(cfg.folder, 'applications', project, 'opt', f'MEDEA_{scenario}_data.gdx')
        db_input.export(export_location)

        # call GAMS
        gms_model = os.path.join(cfg.folder, 'applications', project, 'opt', 'medea_vanilla.gms')
        gdx_out = f'gdx=medea_out_{scenario}.gdx'
        # subprocess.run(f'{cfg.gams_sysdir}\\gams {gms_model} {gdx_out} lo=3 --scenario={scenario}')

        # delete input
        # if os.path.isfile(export_location):
        #    os.remove(export_location)