import logging

import pandas as pd
import yaml

from logging_config import setup_logging
from src.tools.data_processing import download_file, medea_path

setup_logging()

credentials = yaml.load(open(medea_path('credentials.yml')), Loader=yaml.SafeLoader)
api_key = credentials['quandl']['apikey']

# ======================================================================================================================
# IMF commodity price data
url_imf = 'https://www.imf.org/~/media/Files/Research/CommodityPrices/Monthly/ExternalData.ashx'
imf_file = medea_path('data', 'raw', 'imf_price_data.xlsx')
# ECB foreign exchange data
url_fx = 'https://sdw.ecb.europa.eu/quickviewexport.do?SERIES_KEY=120.EXR.D.USD.EUR.SP00.A&type=xls'
fx_file = medea_path('data', 'raw', 'ecb_fx_data.csv')

logging.info(f'downloading monthly commodity prices from {url_imf}')
download_file(url_imf, imf_file)
df_imf = pd.read_excel(imf_file, index_col=[0], skiprows=[1, 2, 3])
df_imf.index = pd.to_datetime(df_imf.index, format='%YM%m')

logging.info(f'downloading exchange rates from {url_fx}')
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

fuel_price_file = medea_path('data', 'processed', 'monthly_fuel_prices.csv')
df_prices_mwh.to_csv(fuel_price_file)
logging.info(f'fuel prices exported to {fuel_price_file}')

# ======================================================================================================================
# CO2 price data
url_co2 = f'https://www.quandl.com/api/v3/datasets/CHRIS/ICE_C1.csv?api_key={api_key}'
co2_file = medea_path('data', 'raw', 'eua_price.csv')
logging.info(f'downloading EUA prices from {url_co2}')
download_file(url_co2, co2_file)
df_price_co2 = pd.read_csv(co2_file, index_col=[0])
df_price_co2.index = pd.to_datetime(df_price_co2.index, format='%Y-%m-%d')
co2_price_file = medea_path('data', 'processed', 'co2_price.csv')
df_price_co2['Settle'].to_csv(co2_price_file)
logging.info(f'CO2 prices exported to {co2_price_file}')
