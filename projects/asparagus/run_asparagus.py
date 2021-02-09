# %% imports
import os

import pandas as pd
from gams import *

import config as cfg
from projects.asparagus.settings_asparagus import *
from src.utils.gams_io import reset_symbol, gdx2df, df2gdx, run_medea_project

idx = pd.IndexSlice
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
dict_r = {rec.keys[0] for rec in db_input['n']}

# *** read in all parameters to be adjusted ***
INITIAL_CAP_G = gdx2df(db_input, 'INITIAL_CAP_G', ['z', 'i'], [])
INITIAL_CAP_R = gdx2df(db_input, 'INITIAL_CAP_R', ['z', 'n'], [])
DEMAND = gdx2df(db_input, 'DEMAND', ['z', 't', 'm'], [])
GEN_PROFILE = gdx2df(db_input, 'GEN_PROFILE', ['z', 't', 'n'], [])

# %% generate 'dynamic' parameter variations (modifications that constitute the scenarios, i.e. that change across runs)
# -------------------------------------------------------------------------------------------------------------------- #
# ensure that we are in the correct model directory
os.chdir(os.path.join(cfg.MEDEA_ROOT_DIR, 'projects', PROJECT_NAME, 'opt'))

# create empty scenario parameter in GAMS database so that it can be modified subsequently
CO2_SCENARIO = df2gdx(db_input, pd.DataFrame(data=[0]), 'CO2_SCENARIO', 'par', 0, 'CO2 price scenario')
WIND_ON_LIMIT = df2gdx(db_input, pd.DataFrame(data=[0]), 'WIND_ON_LIMIT', 'par', 0, 'max wind_on capacity addition')
PV_CAPEX = df2gdx(db_input, pd.DataFrame(data=[0]), 'PV_CAPEX', 'par', 0, 'capex for solar PV at 5.5% interest')
SWITCH_ANCILLARY = df2gdx(db_input, pd.DataFrame(data=[0]), 'SWITCH_ANCILLARY', 'par', 0, 'CO2 price scenario')
SWITCH_POLICY = df2gdx(db_input, pd.DataFrame(data=[1]), 'SWITCH_POLICY', 'par', 0, 'switch for policy constraint')
INITIAL_CAP_X = pd.DataFrame(data=0, columns=['Value'], index=pd.MultiIndex.from_product([cfg.zones, cfg.zones]))
FLOW_LIMIT = df2gdx(db_input, pd.DataFrame(data=[0]), 'FLOW_LIMIT', 'par', 0,
                    'max transmission expansion')

# iterate over all campaigns in dict_campaigns and 'sub-scenarios' for
# a) co2-price,
# b) admissible wind power expansion, and
# c) pv overnight cost

for campaign in dict_campaigns.keys():
    # update campaign dictionary
    dict_camp = dict_base.copy()
    dict_camp.update(dict_campaigns[campaign])

    # do not adjust capacities if we are running a campaign for 2016
    # modify INITIAL_CAP_G
    INIT_CAP_G = INITIAL_CAP_G.copy()
    if '2016' not in campaign:
        for z in cfg.zones:
            for gen in INIT_CAP_G.loc[z].index:
                INIT_CAP_G.loc[idx[z, gen]] = INITIAL_CAP_G.loc[idx[z, gen]] * scenario_2030[z][gen.split('_')[0]][0]
    reset_symbol(db_input, 'INITIAL_CAP_G', INIT_CAP_G)

    # modify INITIAL_CAP_R
    INIT_CAP_R = INITIAL_CAP_R.copy()
    if '2016' not in campaign:
        for z in cfg.zones:
            for itm in dict_r:
                #        if itm != 'ror':
                INIT_CAP_R.loc[idx[z, itm], :] = scenario_2030[z][itm][0]
    reset_symbol(db_input, 'INITIAL_CAP_R', INIT_CAP_R)
    print(INIT_CAP_R)

    # set campaign-parameters for:
    # 1) electricity demand,
    DEM = DEMAND
    d_factor = dict_camp['d_power'][0] / DEMAND.loc[idx['AT', :, 'el'], :].sum()
    DEM.loc[idx['AT', :, 'el'], :] = DEM.loc[idx['AT', :, 'el'], :] * d_factor
    reset_symbol(db_input, 'DEMAND', DEM)
    # 2) transmission capacity,
    INIT_CAP_X = INITIAL_CAP_X
    for z in cfg.zones:
        for zz in cfg.zones:
            if z != zz:
                INIT_CAP_X.loc[idx[z, zz]] = dict_camp['transmission'][0]
    reset_symbol(db_input, 'INITIAL_CAP_X', INIT_CAP_X)
    # 3) must-run
    reset_symbol(db_input, 'SWITCH_ANCILLARY', pd.DataFrame(data=dict_camp['must_run']))
    # 4) policy constraint
    reset_symbol(db_input, 'SWITCH_POLICY', pd.DataFrame(data=dict_camp['policy']))

    # if campaign == 'pv_upscale':
    #     GEN_PROFILE = GEN_PROFILE.unstack(['z', 'n'])
    #     GEN_PROFILE = time_sort(GEN_PROFILE)
    #     GEN_PROFILE = GEN_PROFILE.stack(['z', 'n']).reorder_levels(['z', 't', 'n'])
    #     reset_symbol(db_input, 'GEN_PROFILE', GEN_PROFILE)

    # a) co2-price
    for price_co2 in dict_camp['co2_price']:
        reset_symbol(db_input, 'CO2_SCENARIO', pd.DataFrame(data=[price_co2]))
        # b) admissible wind power expansion
        for wind_limit in dict_camp['wind_cap']:
            # modify upper limit for wind installation
            reset_symbol(db_input, 'WIND_ON_LIMIT', pd.DataFrame(data=[wind_limit]))
            # c) pv overnight cost
            for pv_capex in dict_camp['pv_cost']:
                # modify pv overnight cost
                reset_symbol(db_input, 'PV_CAPEX', pd.DataFrame(data=[pv_capex]))

                # generate identifier / name of scenario
                identifier = f'{PROJECT_NAME}_{campaign}_{price_co2}_{wind_limit}_{pv_capex}'

                # export modified GAMS database to a .gdx-file that is then being read by the GAMS model
                input_fname = os.path.join(cfg.MEDEA_ROOT_DIR, 'projects', PROJECT_NAME, 'opt',
                                           f'medea_{identifier}_data.gdx')
                db_input.export(input_fname)

                # run medea
                run_medea_project(PROJECT_NAME, identifier)
