# %% imports
import os

import pandas as pd
from gams import *

import config as cfg
# from projects.asparagus.preprocess_asparagus import pv_upscaled
from projects.asparagus.settings_asparagus import *
from src.tools.gams_io import reset_symbol, gdx2df, df2gdx, run_medea_project, timesort

# path to main medea model to use
GMS_MODEL = os.path.join(cfg.MEDEA_ROOT_DIR, 'projects', PROJECT_NAME, 'opt', 'medea_main.gms')
# -------------------------------------------------------------------------------------------------------------------- #
# %% initialize GAMS, GAMS workspace and load model data
# -------------------------------------------------------------------------------------------------------------------- #
# import base data from gdx
ws = GamsWorkspace(system_directory=cfg.GMS_SYS_DIR)
db_input = ws.add_database_from_gdx(
    os.path.join(cfg.MEDEA_ROOT_DIR, 'projects', PROJECT_NAME, 'opt', 'medea_main_data.gdx'))

# %% read parameters that change in scenarios (and corresponding sets)
# -------------------------------------------------------------------------------------------------------------------- #
# *** read in all sets over which adjusted parameters are defined ***
# general example for reading a GAMS set from the gdx-database to a python dictionary:
# dict_set = {rec.keys[0] for rec in db_input['set_name']}
# ---
# read sets for calibration of power plant efficiencies
dict_m = {rec.keys[0] for rec in db_input['m']}
dict_f = {rec.keys[0] for rec in db_input['f']}
dict_i = {rec.keys[0] for rec in db_input['i']}
dict_r = {rec.keys[0] for rec in db_input['n']}

# *** read in all parameters to be adjusted ***
# general example for reading parameter 'PARAMETER_NAME' defined over 'set_name' to pandas DataFrame df
# df = gdx2df(db_input, 'PARAMETER_NAME', ['set_name'], [])
# ---
EFFICIENCY_G = gdx2df(db_input, 'EFFICIENCY_G', ['i', 'm', 'f'], [])
FEASIBLE_INPUT = gdx2df(db_input, 'FEASIBLE_INPUT', ['i', 'l', 'f'], [])
INITIAL_CAP_G = gdx2df(db_input, 'INITIAL_CAP_G', ['z', 'i'], [])
INITIAL_CAP_R = gdx2df(db_input, 'INITIAL_CAP_R', ['z', 'n'], [])
DEMAND = gdx2df(db_input, 'DEMAND', ['z', 't', 'm'], [])
GEN_PROFILE = gdx2df(db_input, 'GEN_PROFILE', ['z', 't', 'n'], [])

# %% generate 'static' parameter variations (modifications that remain the same across all scenarios)
# -------------------------------------------------------------------------------------------------------------------- #
# example: calibrate power plant efficiencies -- note: calibration remains the same across all scenarios!
# efficiency -dictionary needs to be imported from settings_{project_name}.py
idx = pd.IndexSlice
fuel_thermal = ['Biomass', 'Coal', 'Gas', 'Lignite', 'Nuclear', 'Oil']

# modify power plant efficiency
EFF_G = EFFICIENCY_G.copy()
for fl in fuel_thermal:
    EFF_G.loc[idx[:, :, fl], :] = EFFICIENCY_G.loc[idx[:, :, fl], :] * efficiency[f'e_{fl}'][0]
reset_symbol(db_input, 'EFFICIENCY_G', EFF_G)

# modify fuel requirement of co-generation plants
fuel_chp = FEASIBLE_INPUT.index.get_level_values(2).unique()
FEAS_IN = FEASIBLE_INPUT.copy()
for fl in fuel_chp:
    FEAS_IN.loc[idx[:, :, fl], :] = FEASIBLE_INPUT.loc[idx[:, :, fl], :] / efficiency[f'e_{fl}'][0]
reset_symbol(db_input, 'FEASIBLE_INPUT', FEAS_IN)

# modify INITIAL_CAP_G
INIT_CAP_G = INITIAL_CAP_G
for z in cfg.zones:
    for gen in INITIAL_CAP_G.loc[z].index:
        INIT_CAP_G.loc[idx[z, gen]] = INITIAL_CAP_G.loc[idx[z, gen]] * scenario_2030[z][gen.split('_')[0]][0]
reset_symbol(db_input, 'INITIAL_CAP_G', INIT_CAP_G)

# modify INITIAL_CAP_R
INIT_CAP_R = INITIAL_CAP_R
for z in cfg.zones:
    for itm in dict_r:
        #        if itm != 'ror':
        INIT_CAP_R.loc[idx[z, itm], :] = scenario_2030[z][itm][0]
reset_symbol(db_input, 'INITIAL_CAP_R', INIT_CAP_R)

# modify DEMAND
DEM = DEMAND
d_factor = scenario_2030['AT']['d_power'][0] / DEMAND.loc[idx['AT', :, 'el'], :].sum()
DEM.loc[idx['AT', :, 'el'], :] = DEM.loc[idx['AT', :, 'el'], :] * d_factor
reset_symbol(db_input, 'DEMAND', DEM)

# %% generate 'dynamic' parameter variations (modifications that constitute the scenarios, i.e. that change each run)
# -------------------------------------------------------------------------------------------------------------------- #
# ensure that we are in the correct model directory
os.chdir(os.path.join(cfg.MEDEA_ROOT_DIR, 'projects', PROJECT_NAME, 'opt'))

# create empty scenario parameter in GAMS database so that it can be modified subsequently
# example: changing CO2 price
CO2_SCENARIO = df2gdx(db_input, pd.DataFrame(data=[0]), 'CO2_SCENARIO', 'par', 0, 'CO2 price scenario')
WIND_ON_LIMIT = df2gdx(db_input, pd.DataFrame(data=[0]), 'WIND_ON_LIMIT', 'par', 0, 'max wind_on capacity addition')
PV_CAPEX = df2gdx(db_input, pd.DataFrame(data=[0]), 'PV_CAPEX', 'par', 0, 'capex for solar PV at 5.5% interest')
SWITCH_ANCILLARY = df2gdx(db_input, pd.DataFrame(data=[0]), 'SWITCH_ANCILLARY', 'par', 0, 'CO2 price scenario')
SWITCH_POLICY = df2gdx(db_input, pd.DataFrame(data=[1]), 'SWITCH_POLICY', 'par', 0, 'switch for policy constraint')
INITIAL_CAP_X = pd.DataFrame(data=0, columns=['Value'], index=pd.MultiIndex.from_product([cfg.zones, cfg.zones]))
FLOW_LIMIT = df2gdx(db_input, pd.DataFrame(data=[0]), 'FLOW_LIMIT', 'par', 0,
                    'max transmission expansion')
# iterate over scenario dictionary
for campaign in dict_campaigns.keys():
    # modify scenario parameter and solve medea for each scenario (i.e. for each parameter modification)
    reset_symbol(db_input, 'SWITCH_ANCILLARY', pd.DataFrame(data=dict_campaigns[campaign]['must_run']))
    reset_symbol(db_input, 'SWITCH_POLICY', pd.DataFrame(data=dict_campaigns[campaign]['policy']))

    INIT_CAP_X = INITIAL_CAP_X
    for z in cfg.zones:
        for zz in cfg.zones:
            if z != zz:
                INIT_CAP_X.loc[idx[z, zz]] = dict_campaigns[campaign]['transmission'][0]
    reset_symbol(db_input, 'INITIAL_CAP_X', INIT_CAP_X)

    if campaign == 'pv_upscale':
        GEN_PROFILE = GEN_PROFILE.unstack(['z', 'n'])
        GEN_PROFILE = timesort(GEN_PROFILE)
        # pv_upscaled.index = GEN_PROFILE.index
        # GEN_PROFILE.loc[:, idx['Value', 'AT', 'pv']] = pv_upscaled.values
        GEN_PROFILE = GEN_PROFILE.stack(['z', 'n']).reorder_levels(['z', 't', 'n'])
        reset_symbol(db_input, 'GEN_PROFILE', GEN_PROFILE)

    for price_co2 in dict_campaigns[campaign]['co2_price']:
        # modify scenario parameter in GAMS database
        # example: change CO2 price
        reset_symbol(db_input, 'CO2_SCENARIO', pd.DataFrame(data=[price_co2]))

        for wind_limit in dict_campaigns[campaign]['wind_cap']:
            # modify upper limit for wind installation
            reset_symbol(db_input, 'WIND_ON_LIMIT', pd.DataFrame(data=[wind_limit]))

            for pv_capex in dict_campaigns[campaign]['pv_cost']:
                # generate identifier / name of scenario
                identifier = f'{PROJECT_NAME}_{campaign}_{price_co2}_{wind_limit}_{pv_capex}'

                # modify upper limit for wind installation
                reset_symbol(db_input, 'PV_CAPEX', pd.DataFrame(data=[pv_capex]))

                # export modified GAMS database to a .gdx-file that is then being read by the GAMS model
                input_fname = os.path.join(cfg.MEDEA_ROOT_DIR, 'projects', PROJECT_NAME, 'opt',
                                           f'medea_{identifier}_data.gdx')
                db_input.export(input_fname)

                # run medea
                run_medea_project(PROJECT_NAME, identifier)
