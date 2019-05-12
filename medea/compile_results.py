import os

import pandas as pd
from gams import *

import config as cfg
from medea.gams_wrappers import gdx2df

output_folder = 'PolicyBurden'
campaign_string = 'PoBu_maxwind_AT_'
directory = os.path.join(cfg.folder, 'medea', 'opt')

ws = GamsWorkspace(system_directory=cfg.gams_sysdir)
# for file in os.listdir(directory):
#     filename = os.fsdecode(file)
#     if campaign_string in filename:

df_all = pd.DataFrame()
for num in range(0, 12):
    filename = f'medea_out_{campaign_string}{num}.gdx'
    db_output = ws.add_database_from_gdx(os.path.join(cfg.folder, 'medea', 'opt', filename))

    read_variables = {
        'cost': ([], ['r']),
        'emissions': ([], ['r']),
        'invest_res': (['tec_itm'], ['r']),
        'invest_thermal': (['tec'], ['r']),
        'ntc_invest': (['r'], ['r']),
        'annual_price_el': ([], ['r']),
        'annual_price_ht': ([], ['r']),
        'annual_pumping': ([], ['r']),
        'annual_turbining': ([], ['r']),
        'annual_generation': (['prd'], ['r']),
        'annual_curtail': ([], ['r']),
        'annual_netflow': ([], ['r']),
        'producer_surplus': ([], ['r']),
    }

    result_dict = {key: gdx2df(db_output, key, value[0], value[1])
                   for key, value in read_variables.items()}

    df = pd.DataFrame(columns=['AT', 'DE'])
    for key, value in result_dict.items():
        if value.index.any() == 'Value':
            value.index = [key]
        df = df.append(value)
    df.columns = pd.MultiIndex.from_product([[f'WOn_{num}'], df.columns])
    df_all = pd.concat([df_all, df], axis=1)

df_all = df_all.sort_index(axis=1, level=1)
df_all.to_csv(os.path.join(cfg.folder, 'medea', 'output', output_folder, f'results_{campaign_string}.csv'),
              sep=';', encoding='utf-8')