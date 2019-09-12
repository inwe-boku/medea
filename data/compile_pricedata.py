import os

import pandas as pd

import config as cfg

df_fuels = pd.read_excel(os.path.join(cfg.MEDEA_ROOT_DIR, 'data', 'raw', 'monthly_fuel_prices.xlsx'), 'fuels_monthly',
                         skiprows=[1, 2])  # , parse_dates=True)
df_fuels.set_index('Date', inplace=True)

df_fuelprices = df_fuels[['Ngas_Border_MWh', 'Coal_Import_MWh', 'Brent_MWh', 'Coal_SA_MWh', 'NGas_Europe_MWh']]
df_fuelprices = df_fuelprices.resample('H').interpolate('pchip')

