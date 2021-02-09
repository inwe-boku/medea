import os

import pandas as pd
from gams import *

import config as cfg
from projects.opco.settings_opco import *
from src.utils.data_processing import medea_path
from src.utils.gams_io import reset_symbol, df2gdx, run_medea_project

idx = pd.IndexSlice
# -------------------------------------------------------------------------------------------------------------------- #
# %% initialize GAMS, GAMS workspace and load model data
# -------------------------------------------------------------------------------------------------------------------- #
# import base data from gdx
ws = GamsWorkspace(system_directory=cfg.GMS_SYS_DIR)
db_input = ws.add_database_from_gdx(
    os.path.join(cfg.MEDEA_ROOT_DIR, 'projects', PROJECT_NAME, 'opt', 'medea_main_data.gdx'))
# db_input = ws.add_database_from_gdx(medea_path('projects', PROJECT_NAME, 'opt', 'medea_main_data.gdx'))


# %% read parameters that change in scenarios (and corresponding sets)
# -------------------------------------------------------------------------------------------------------------------- #
# *** read in all sets over which adjusted parameters are defined ***
# general example for reading a GAMS set from the gdx-database to a python dictionary:
# dict_set = {rec.keys[0] for rec in db_input['set_name']}
# ---

# *** read in all parameters to be adjusted ***
# general example for reading parameter 'PARAMETER_NAME' defined over 'set_name' to pandas DataFrame df
# df = gdx2df(db_input, 'PARAMETER_NAME', ['set_name'], [])
# ---

# fuel_thermal = ['Biomass', 'Coal', 'Gas', 'Lignite', 'Nuclear', 'Oil']


# %% generate 'dynamic' parameter variations (modifications that constitute the scenarios, i.e. that change each run)
# -------------------------------------------------------------------------------------------------------------------- #
# ensure that we are in the correct model directory
os.chdir(medea_path('projects', PROJECT_NAME, 'opt'))

# create empty scenario parameter in GAMS database so that it can be modified subsequently
RE_SHARE = df2gdx(db_input, pd.DataFrame(data=[0]), 'RE_SHARE', 'par', 0, 'Minimum share of RE generation')
WIND_ON_LIMIT = df2gdx(db_input, pd.DataFrame(data=[0]), 'WIND_ON_LIMIT', 'par', 0, 'max wind_on capacity addition')
CO2_BUDGET = df2gdx(db_input, pd.DataFrame(data=[0]), 'CO2_BUDGET', 'par', 0, 'max amount of co2 emitted')
CO2_SCENARIO = df2gdx(db_input, pd.DataFrame(data=[0]), 'CO2_SCENARIO', 'par', 0, 'CO2 price scenario')
SWITCH_ANCILLARY = df2gdx(db_input, pd.DataFrame(data=[0]), 'SWITCH_ANCILLARY', 'par', 0,
                          'switch to activate ancillary service demand')

# modify scenario parameter and solve medea for each scenario (i.e. for each parameter modification)

for campaign in dict_campaigns.keys():
    # update campaign dictionary
    dict_camp = dict_base.copy()
    dict_camp.update(dict_campaigns[campaign])

    # (de)activate must-run
    reset_symbol(db_input, 'SWITCH_ANCILLARY', pd.DataFrame(data=dict_camp['must_run']))
    # set campaign-parameters
    for re_share in dict_camp['re_share']:
        reset_symbol(db_input, 'RE_SHARE', pd.DataFrame(data=[re_share]))

        for wind_limit in dict_camp['wind_on_cap']:
            reset_symbol(db_input, 'WIND_ON_LIMIT', pd.DataFrame(data=[wind_limit]))

            for price_co2 in dict_camp['carbon_price']:
                reset_symbol(db_input, 'CO2_SCENARIO', pd.DataFrame(data=[price_co2]))

                for budget_co2 in dict_camp['carbon_limit']:
                    reset_symbol(db_input, 'CO2_BUDGET', pd.DataFrame(data=[budget_co2]))

                    # generate identifier / name of scenario
                    identifier = f'{PROJECT_NAME}_{campaign}_{re_share}_{wind_limit}_{price_co2}_{budget_co2}'

                    # export modified GAMS database to a .gdx-file that is then being read by the GAMS model
                    input_fname = os.path.join(cfg.MEDEA_ROOT_DIR, 'projects', PROJECT_NAME, 'opt',
                                               f'medea_{identifier}_data.gdx')
                    db_input.export(input_fname)

                    # run medea
                    run_medea_project(PROJECT_NAME, identifier)
