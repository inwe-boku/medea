import os
import subprocess
import pandas as pd
from gams import *

import config as cfg
from medea.gams_io import reset_parameter, gdx2df, df2gdx
# import project settings, user must replace {project_name} by corresponding project name
from applications.{project_name}.settings_{project_name} import *

project_name = 'pass_through'  # 'project_name'
# -------------------------------------------------------------------------------------------------------------------- #


# %% initialize GAMS, GAMS workspace and load model data
# -------------------------------------------------------------------------------------------------------------------- #
# import base data from gdx
ws = GamsWorkspace(system_directory=cfg.gams_sysdir)
db_input = ws.add_database_from_gdx(os.path.join(cfg.folder, 'applications', project_name, 'opt', 'medea_main_data.gdx'))


# %% read parameters that change in scenarios (and corresponding sets)
# -------------------------------------------------------------------------------------------------------------------- #
# *** read in all sets over which adjusted parameters are defined ***
# general example for reading a GAMS set from the gdx-database to a python dictionary:
# dict_set = {rec.keys[0] for rec in db_input['set_name']}
# ---
# read sets for calibration of power plant efficiencies
dict_prd = {rec.keys[0] for rec in db_input['prd']}
dict_fuel = {rec.keys[0] for rec in db_input['f']}
dict_tec = {rec.keys[0] for rec in db_input['tec']}

# *** read in all parameters to be adjusted ***
# general example for reading parameter 'PARAMETER_NAME' defined over 'set_name' to pandas DataFrame df
# df = gdx2df(db_input, 'PARAMETER_NAME', ['set_name'], [])
# ---
# read power plant efficiency data
df_eff = gdx2df(db_input, 'EFFICIENCY', ['tec', 'prd', 'f'], [])
# read fuel requirement of CHP plants-data
df_fuelreq = gdx2df(db_input, 'FEASIBLE_INPUT', ['tec', 'l', 'f'], [])


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
reset_parameter(db_input, 'EFFICIENCY', df_eff_mod)

# modify fuel requirement of co-generation plants
df_fuelreq_mod = df_fuelreq.copy()
for fl in fuel_thermal:
    df_fuelreq_mod.loc[idx[:, :, fl], :] = \
        df_fuelreq.loc[idx[:, :, fl], :] / efficiency[f'e_{fl}'][0]
reset_parameter(db_input, 'FEASIBLE_INPUT', df_fuelreq_mod)

# %% generate 'dynamic' parameter variations (modifications that constitute the scenarios, i.e. that change each run)
# -------------------------------------------------------------------------------------------------------------------- #
# ensure that we are in the correct model directory
os.chdir(os.path.join(cfg.folder, 'applications', project_name, 'opt'))

# create empty scenario parameter in GAMS database so that it can be modified subsequently
# example: changing CO2 price
scenario_co2 = df2gdx(db_input, pd.DataFrame(data=[0]), 'EUA_SCENARIO', 'par', 0, 'CO2 price scenario')

# modify scenario parameter and solve medea for each scenario (i.e. for each parameter modification)
for price_co2 in range_co2price:
    # generate identifier / name of scenario
    identifier = output_naming.format(price_co2)

    # modify scenario parameter in GAMS database
    # example: change CO2 price
    reset_parameter(db_input, 'EUA_SCENARIO', pd.DataFrame(data=[price_co2]))

    # export modified GAMS database to a .gdx-file that is then being read by the GAMS model
    export_location = os.path.join(cfg.folder, 'applications', project_name, 'opt', f'medea_{identifier}_data.gdx')
    db_input.export(export_location)

    # generate path to medea model
    gms_model = os.path.join(cfg.folder, 'applications', project_name, 'opt', 'medea_main.gms')

    # generate identifier of scenario output
    gdx_out = f'gdx=medea_out_{identifier}.gdx'

    # call GAMS to solve model / scenario
    subprocess.run(
        f'{cfg.gams_sysdir}\\gams {gms_model} {gdx_out} lo=3 --project={project_name} --scenario={identifier}')

    # clean up after each run and delete input data (which is also included in output, so no information lost)
    if os.path.isfile(export_location):
        os.remove(export_location)
