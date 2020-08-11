import os
import subprocess

import pandas as pd
from gams import *

import config as cfg
from src.templates.settings_template import *
from src.tools.data_processing import medea_path
from src.tools.gams_io import reset_symbol, gdx2df, df2gdx

# -------------------------------------------------------------------------------------------------------------------- #
# %% initialize GAMS, GAMS workspace and load model data
# -------------------------------------------------------------------------------------------------------------------- #
# import base data from gdx
ws = GamsWorkspace(system_directory=cfg.GMS_SYS_DIR)
db_input = ws.add_database_from_gdx(medea_path('projects', project_name, 'opt', 'medea_main_data.gdx'))


# %% read parameters that change in scenarios (and corresponding sets)
# -------------------------------------------------------------------------------------------------------------------- #
# *** read in all sets over which adjusted parameters are defined ***
# general example for reading a GAMS set from the gdx-database to a python dictionary:
# dict_set = {rec.keys[0] for rec in db_input['set_name']}
# ---
# read sets for calibration of power plant efficiencies
dict_prd = {rec.keys[0] for rec in db_input['m']}
dict_fuel = {rec.keys[0] for rec in db_input['f']}
dict_tec = {rec.keys[0] for rec in db_input['i']}

# *** read in all parameters to be adjusted ***
# general example for reading parameter 'PARAMETER_NAME' defined over 'set_name' to pandas DataFrame df
# df = gdx2df(db_input, 'PARAMETER_NAME', ['set_name'], [])
# ---
# read power plant efficiency data
df_eff = gdx2df(db_input, 'EFFICIENCY_G', ['i', 'm', 'f'], [])
# read fuel requirement of CHP plants-data
df_fuelreq = gdx2df(db_input, 'FEASIBLE_INPUT', ['i', 'l', 'f'], [])


# %% generate 'static' parameter variations (modifications that remain the same across all scenarios)
# -------------------------------------------------------------------------------------------------------------------- #
# example: calibrate power plant efficiencies -- note: calibration remains the same across all scenarios!
# efficiency -dictionary needs to be imported from settings_{project_name}.py
idx = pd.IndexSlice
fuel_thermal = ['Biomass', 'Coal', 'Gas', 'Lignite', 'Nuclear', 'Oil']

# modify power plant efficiency
df_eff_mod = df_eff.copy()
for fl in fuel_thermal:
    df_eff_mod.loc[idx[:, :, fl], :] = \
        df_eff.loc[idx[:, :, fl], :] * efficiency[f'e_{fl}'][0]
reset_symbol(db_input, 'EFFICIENCY_G', df_eff_mod)

# modify fuel requirement of co-generation plants
df_fuelreq_mod = df_fuelreq.copy()
for fl in fuel_thermal:
    df_fuelreq_mod.loc[idx[:, :, fl], :] = \
        df_fuelreq.loc[idx[:, :, fl], :] / efficiency[f'e_{fl}'][0]
reset_symbol(db_input, 'FEASIBLE_INPUT', df_fuelreq_mod)

# %% generate 'dynamic' parameter variations (modifications that constitute the scenarios, i.e. that change each run)
# -------------------------------------------------------------------------------------------------------------------- #
# ensure that we are in the correct model directory
os.chdir(medea_path('projects', project_name, 'opt'))

# create empty scenario parameter in GAMS database so that it can be modified subsequently
# example: changing CO2 price
scenario_co2 = df2gdx(db_input, pd.DataFrame(data=[0]), 'CO2_SCENARIO', 'par', 0, 'CO2 price scenario')

# modify scenario parameter and solve medea for each scenario (i.e. for each parameter modification)
for price_co2 in range_co2price:
    # generate identifier / name of scenario
    identifier = output_naming.format(price_co2)

    # modify scenario parameter in GAMS database
    # example: change CO2 price
    reset_symbol(db_input, 'CO2_SCENARIO', pd.DataFrame(data=[price_co2]))

    # export modified GAMS database to a .gdx-file that is then being read by the GAMS model
    export_location = medea_path('projects', project_name, 'opt', f'medea_{identifier}_data.gdx')
    db_input.export(export_location)

    # generate path to medea model
    gms_model = medea_path('projects', project_name, 'opt', 'medea_main.gms')

    # generate identifier of scenario output
    gdx_out = f'gdx=medea_out_{identifier}.gdx'

    # call GAMS to solve model / scenario
    subprocess.run(
        f'{cfg.GMS_SYS_DIR}\\gams {gms_model} {gdx_out} lo=3 --project={project_name} --scenario={identifier}')

    # clean up after each run and delete input data (which is also included in output, so no information lost)
    if os.path.isfile(export_location):
        os.remove(export_location)
