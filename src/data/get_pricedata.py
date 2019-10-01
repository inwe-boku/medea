import os

import pandas as pd

import config as cfg
from src.tools.data_processing import download_file

# ======================================================================================================================
# IMF commodity price data
url_imf = 'https://www.imf.org/~/media/Files/Research/CommodityPrices/Monthly/ExternalData.ashx'
imf_file = os.path.join(cfg.MEDEA_ROOT_DIR, 'data', 'raw', 'imf_price_data.xlsx')
# ECB foreign exchange data
url_fx = 'https://sdw.ecb.europa.eu/quickviewexport.do?SERIES_KEY=120.EXR.D.USD.EUR.SP00.A&type=xls'
fx_file = os.path.join(cfg.MEDEA_ROOT_DIR, 'data', 'raw', 'ecb_fx_data.csv')

download_file(url_imf, imf_file)
df_imf = pd.read_excel(imf_file, index_col=[0], skiprows=[1, 2, 3])
df_imf.index = pd.to_datetime(df_imf.index, format='%YM%m')

download_file(url_fx, fx_file)
df_fx = pd.read_csv(fx_file, header=[0], index_col=[0], skiprows=[0, 2, 3, 4], na_values=['-']).astype('float')
df_fx.index = pd.to_datetime(df_fx.index, format='%Y-%m-%d')

# convert prices to EUR per MWh
df_prices_mwh = pd.DataFrame(index=df_imf.index, columns=['USD_EUR', 'Brent_UK', 'Coal_SA', 'NGas_DE'])
df_prices_mwh['USD_EUR'] = df_fx.resample('MS').mean()
df_prices_mwh['Brent_UK'] = df_imf['POILBRE'] / df_prices_mwh['USD_EUR'] * 7.52 / 11.63
df_prices_mwh['Coal_SA'] = df_imf['PCOALSA_USD'] / df_prices_mwh['USD_EUR'] / 6.97333
df_prices_mwh['NGas_DE'] = df_imf['PNGASEU'] / df_prices_mwh['USD_EUR'] / 0.29307
# drop rows with all nan
df_prices_mwh.dropna(how='all', inplace=True)

df_prices_mwh.to_csv(os.path.join(cfg.MEDEA_ROOT_DIR, 'data', 'processed', 'monthly_fuel_prices.csv'))

# ======================================================================================================================
# CO2 price data
url_co2 = 'https://www.quandl.com/api/v3/datasets/CHRIS/ICE_C1.csv?api_key=ZjVrsf1p6TCzq-_JUFQd'
co2_file = os.path.join(cfg.MEDEA_ROOT_DIR, 'data', 'raw', 'eua_price.csv')
download_file(url_co2, co2_file)
df_price_co2 = pd.read_csv(co2_file, index_col=[0])
df_price_co2.index = pd.to_datetime(df_price_co2.index, format='%Y-%m-%d')
df_price_co2['Settle'].to_csv(os.path.join(cfg.MEDEA_ROOT_DIR, 'data', 'processed', 'co2_price.csv'))
