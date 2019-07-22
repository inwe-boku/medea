import os
import pandas as pd
from gams import *

import config as cfg
from applications.pass_through.settings_pass_through import project, eua_range, capacity_scenario_name, output_naming
from medea.gams_io import gdx2df

# %% Preparations & Settings
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
    # 'annual_price_ht': ([], ['r']),
    'annual_pumping': ([], ['r']),
    'annual_turbining': ([], ['r']),
    'annual_generation': (['prd'], ['r']),
    # 'annual_curtail': ([], ['r']),
    'annual_netflow': ([], ['r']),
    'producer_surplus': ([], ['r']),
    'hourly_price_el': (['t'], ['r'])
}

df_all = pd.DataFrame()
for scenario in capacity_scenario_name:

    for peua in eua_range:
        filename = f'medea_out_{output_naming}.gdx'.format(scenario, peua)
        db_output = ws.add_database_from_gdx(os.path.join(cfg.folder, 'applications', project, 'opt', filename))

        result_dict = {key: gdx2df(db_output, key, value[0], value[1])
                       for key, value in read_variables.items()}

        df = pd.DataFrame(columns=cfg.regions)
        for key, value in result_dict.items():
            if value.index.any() == 'Value':
                value.index = [key]
            df = df.append(value)
#        df.columns = pd.MultiIndex.from_product([[f'WOn_{wind_limit}'], df.columns])
#        df_all = pd.concat([df_all, df], axis=1)

### plotting function
# convert t1 to t8760 back to time units


"""
df_all = df_all.sort_index(axis=1, level=1)
df_all.to_csv(os.path.join(cfg.folder, 'applications', project, 'output',
                           f'out_{scenario}_{peua}.csv'), sep=';', encoding='utf-8')
"""
