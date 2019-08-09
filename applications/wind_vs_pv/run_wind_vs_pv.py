import os
import subprocess
from shutil import copyfile

import pandas as pd
from gams import *

import config as cfg
from applications.wind_vs_pv.settings_wind_vs_pv import *
from medea.gams_io import reset_parameter, gdx2df, df2gdx

# ---------------------------------------------------------------
# %% initialize GAMS, GAMS workspace & load model data

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
df_eua = gdx2df(db_input, 'PRICE_CO2', ['t'], [])
df_capitm = gdx2df(db_input, 'INSTALLED_CAP_ITM', ['z', 'tec_itm'], [])
df_eff = gdx2df(db_input, 'EFFICIENCY', ['tec', 'prd', 'f'], [])
df_feasgen = gdx2df(db_input, 'FEASIBLE_OUTPUT', ['tec', 'l', 'prd'], [])
df_cap_therm = gdx2df(db_input, 'INSTALLED_CAP_THERM', ['z', 'tec'], [])
df_fuelreq = gdx2df(db_input, 'FEASIBLE_INPUT', ['tec', 'l', 'f'], [])
df_load = gdx2df(db_input, 'CONSUMPTION', ['z', 't', 'prd'], [])
tec2fuel_map = gdx2df(db_input, 'EFFICIENCY', ['tec', 'f'], ['prd']).reset_index()
tec2fuel_map = tec2fuel_map.loc[tec2fuel_map['tec'].isin(df_feasgen.index.get_level_values(0)), :]

# --------------------------------------------------------------------------- #
# %% scenario generation
idx = pd.IndexSlice

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

# conventional capacities
df_cap_therm_mod = df_cap_therm
for z in cfg.zones:
    for gen in df_cap_therm.loc[z].index:
        df_cap_therm_mod.loc[idx[z, gen]] = (df_cap_therm.loc[idx[z, gen]] *
                                             scenario_2030[z][gen.split('_')[0]][0]).round(0)
reset_parameter(db_input, 'INSTALLED_CAP_THERM', df_cap_therm_mod)

# intermittent capacities
df_capitm_mod = df_capitm
for z in cfg.zones:
    for itm in itm_dict:
        if itm != 'ror':
            df_capitm_mod.loc[idx[z, itm], :] = scenario_2030[z][itm][0]
reset_parameter(db_input, 'INSTALLED_CAP_ITM', df_capitm_mod)

# electric mobility in Austria increases electricity consumption
df_load_mod = df_load
df_load_mod.loc[idx['AT', :, 'el'], :] = df_load_mod.loc[idx['AT', :, 'el'], :] * \
                                            scenario_2030['AT']['d_power'][0]
reset_parameter(db_input, 'CONSUMPTION', df_load_mod)

# --------------------------------------------------------------------------- #
# %% iterate over trade and CO2 price scenarios
os.chdir(os.path.join(cfg.folder, 'applications', project, 'opt'))
EUA_SCENARIO = df2gdx(db_input, pd.DataFrame(data=[0]), 'EUA_SCENARIO', 'par', 0, 'EUA price - scenario')
WIND_ON_LIMIT = df2gdx(db_input, pd.DataFrame(data=[0]), 'WIND_ON_LIMIT', 'par', 0, 'max wind_on capacity addition')
FLOW_LIMIT = df2gdx(db_input, pd.DataFrame(data=[0]), 'FLOW_LIMIT', 'par', 0, 'max wind_on capacity addition')

for wind_limit in scenario_2030['AT']['lim_wind_on']:
    scenario = 'Autarky' if wind_limit == float('inf') else 'Openness'
    reset_parameter(db_input, 'FLOW_LIMIT', pd.DataFrame(data=electricity_exchange[scenario]))

    # modify wind_on limit
    reset_parameter(db_input, 'WIND_ON_LIMIT', pd.DataFrame(data=[wind_limit]))

    # emission prices
    for peua in eua_range:
        reset_parameter(db_input, 'EUA_SCENARIO', pd.DataFrame(data=[peua]))

        # scenario_string = f'{scenario}_eua-{peua}_won-{wind_limit}'
        scenario_string = output_naming.format(scenario, peua, wind_limit)
        # --------------------------------------------------------------------------- #
        # export gdx
        export_location = os.path.join(cfg.folder, 'applications', project, 'opt', f'MEDEA_{scenario_string}_data.gdx')
        db_input.export(export_location)

        # call GAMS
        gms_model = os.path.join(cfg.folder, 'applications', project, 'opt', 'medea_main.gms')
        gdx_out = f'gdx=medea_out_{scenario_string}.gdx'
        gams_call = os.path.join(cfg.gams_sysdir, 'gams')
        subprocess.run(f'{gams_call} {gms_model} {gdx_out} lo=3 --project={project} --scenario={scenario_string}')

        # delete input
        if os.path.isfile(export_location):
            os.remove(export_location)
