import os

import numpy as np
import pandas as pd
from gams import *

import config as cfg
from applications.wind_vs_pv.settings_wind_vs_pv import project, eua_range, scenario_2030, output_naming
from medea.gams_io import gdx2df

# %%
ws = GamsWorkspace(system_directory=cfg.gams_sysdir)

read_variables = {
    'cost': ([], ['r']),
    'emissions': ([], ['r']),
    'invest_res': (['tec_itm'], ['r']),
    'invest_thermal': (['tec'], ['r']),
    'invest_storage_power': (['tec_strg'], ['r']),
    'invest_storage_energy': (['tec_strg'], ['r']),
    'invest_ntc': (['r'], ['r']),
    'annual_price_el': ([], ['r']),
    'annual_price_ht': ([], ['r']),
    'annual_pumping': ([], ['r']),
    'annual_turbining': ([], ['r']),
    'annual_generation': (['prd'], ['r']),
    'annual_curtail': ([], ['r']),
    'annual_netflow': ([], ['r']),
    'producer_surplus': ([], ['r']),
}


# Autarky results
df_aut = pd.DataFrame()
scenario = 'Autarky'
for peua in eua_range:

    wind_limit = float('inf')
    filename = f'medea_out_{output_naming.format(scenario, peua, wind_limit)}.gdx'
    db_output = ws.add_database_from_gdx(os.path.join(cfg.folder, 'applications', project, 'opt', filename))

    result_dict = {key: gdx2df(db_output, key, value[0], value[1])
                   for key, value in read_variables.items()}

    df = pd.DataFrame(columns=cfg.regions)
    for key, value in result_dict.items():
        if value.index.any() == 'Value':
            value.index = [key]
        df = df.append(value, sort=True)
    df.columns = pd.MultiIndex.from_product([[f'EUA_{peua}'], df.columns])
    df_aut = pd.concat([df_aut, df], axis=1)

df_aut = df_aut.replace(False, np.nan)
df_aut = df_aut.dropna(axis=1, how='all')
df_aut = df_aut.sort_index(axis=1, level=1)
df_aut.to_csv(os.path.join(cfg.folder, 'applications', project, 'results',
                           f'out_{scenario}.csv'), sep=';', encoding='utf-8', decimal=',')

# Openness results
scenario = 'Openness'
for peua in eua_range:
    df_all = pd.DataFrame()
    for wind_limit in scenario_2030['AT']['lim_wind_on']:
        if wind_limit != float('inf'):
            filename = f'medea_out_{output_naming.format(scenario, peua, wind_limit)}.gdx'
            db_output = ws.add_database_from_gdx(os.path.join(cfg.folder, 'applications', project, 'opt', filename))

            result_dict = {key: gdx2df(db_output, key, value[0], value[1])
                           for key, value in read_variables.items()}

            df = pd.DataFrame(columns=cfg.regions)
            for key, value in result_dict.items():
                if value.index.any() == 'Value':
                    value.index = [key]
                df = df.append(value, sort=True)
            df.columns = pd.MultiIndex.from_product([[f'WOn_{wind_limit}'], df.columns])
            df_all = pd.concat([df_all, df], axis=1)

    df_all = df_all.replace(False, np.nan)
    df_all = df_all.dropna(axis=1, how='all')
    df_all = df_all.sort_index(axis=1, level=1)
    df_all.to_csv(os.path.join(cfg.folder, 'applications', project, 'results',
                               f'out_{scenario}_EUA_{peua}.csv'), sep=';', encoding='utf-8', decimal=',')
