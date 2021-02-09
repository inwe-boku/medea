import os

import pandas as pd

import config as cfg
from src.utils.data_processing import medea_path

directory = medea_path('data', 'raw', 'AggregateFillingRateWaterReservoirs')

df_resfill = pd.DataFrame()

for file in os.listdir(directory):
    filename = os.fsdecode(file)
    print(filename)
    if filename.endswith('.csv'):
        # read data
        df_fill = pd.read_csv(medea_path('data', 'raw', 'AggregateFillingRateWaterReservoirs', filename),
                              sep='\t', encoding='utf-16')
        df_fill.index = pd.DatetimeIndex(df_fill['DateTime'])
        df_fillreg = pd.DataFrame(columns=cfg.zones)
        for reg in cfg.zones:
            df_fillreg[f'{reg}'] = df_fill.loc[df_fill['MapCode'] == reg, 'StoredEnergy'].drop_duplicates()

        df_resfill = df_resfill.append(df_fillreg)

df_resfill = df_resfill.sort_index()

# eliminate data errors for Austrian reservoirs filled below 200000
df_resfill.loc[df_resfill['AT'] < 200000, 'AT'] = None
df_resfill = df_resfill.interpolate(method='pchip')

df_resfill.to_csv(medea_path('data', 'processed', 'reservoir_filling.csv'))
