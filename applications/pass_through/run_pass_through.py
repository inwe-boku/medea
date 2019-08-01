# -*- coding: utf-8 -*-
"""
use medea to estimate emission cost pass-through to electricity prices in the current and future electricity systems of Germany and Austria
@author: sweer
"""

import os
import subprocess
from shutil import copyfile

import pandas as pd
from gams import *

import config as cfg
from applications.pass_through.settings_pass_through import *
from medea.gams_io import reset_parameter, gdx2df, df2gdx

# --------------------------------------------------------------------------- #
# %% initialize GAMS, GAMS workspace and load model data
# --------------------------------------------------------------------------- #
# fetch main gams model, if required
if not os.path.isfile(os.path.join(cfg.folder, 'applications', project, 'opt', 'medea_main.gms')):
    copyfile(os.path.join(cfg.folder, 'medea', 'medea_main.gms'),
             os.path.join(cfg.folder, 'applications', project, 'opt', 'medea_main.gms'))
# fetch main gams data, if required
if not os.path.isfile(os.path.join(cfg.folder, 'applications', project, 'opt', 'medea_main_data.gdx')):
    copyfile(os.path.join(cfg.folder, 'medea', 'data', 'input', 'medea_main_data.gdx'),
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
    for reg in cfg.zones:
        for gen in df_num.loc[reg].index:
            df_num_mod.loc[idx[reg, gen]] = (df_num.loc[idx[reg, gen]] *
                                             capacity_scenarios[reg][gen.split('_')[0]][cap_scenario]).round(0)

    reset_parameter(db_input, 'NUM', df_num_mod)

    # renewable capacities
    df_capitm_mod = df_capitm
    for reg in cfg.zones:
        for itm in itm_dict:
            if itm != 'ror':
                df_capitm_mod.loc[idx[reg, itm], :] = capacity_scenarios[reg][itm][cap_scenario]

    reset_parameter(db_input, 'INSTALLED_CAP_ITM', df_capitm_mod)

    # emission prices
    for peua in eua_range:
        reset_parameter(db_input, 'EUA_SCENARIO', pd.DataFrame(data=[peua]))

        scenario_string = output_naming.format(capacity_scenario_name[cap_scenario], peua)
        # --------------------------------------------------------------------------- #
        # export gdx
        export_location = os.path.join(cfg.folder, 'applications', project, 'opt', f'MEDEA_{scenario_string}_data.gdx')
        db_input.export(export_location)

        # call GAMS
        gms_model = os.path.join(cfg.folder, 'applications', project, 'opt', 'medea_main.gms')
        gdx_out = f'gdx=medea_out_{scenario_string}.gdx'
        subprocess.run(f'{cfg.gams_sysdir}\\gams {gms_model} {gdx_out} lo=3 --project={project} --scenario={scenario_string}')

        # delete input
        if os.path.isfile(export_location):
            os.remove(export_location)
