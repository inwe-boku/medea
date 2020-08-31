# %% imports
import logging
import os
import shutil
from pathlib import Path

import cdsapi
import certifi
import numpy as np
import pandas as pd
import urllib3

import config as cfg


# ======================================================================================================================
# %% leap year functions
# ----------------------------------------------------------------------------------------------------------------------

def is_leapyear(year):
    """
    determines whether a given year is a leap year
    :param year: year to check (numeric)
    :return: boolean
    """
    flag = year % 400 == 0 or (year % 4 == 0 and year % 100 != 0)
    return flag


def days_in_year(year):
    """
    returns number of days in a given year
    :param year: year of interest (numeric)
    :return: number of days in year (numeric)
    """
    if is_leapyear(year):
        return 366
    else:
        return 365


def hours_in_year(year):
    """
    returns number of hours in a goven year
    :param year: year of interest (numeric)
    :return: number of hours in year (numeric)
    """
    if is_leapyear(year):
        return 8784
    else:
        return 8760


# ======================================================================================================================
# %% functions for heat load calculation
# ----------------------------------------------------------------------------------------------------------------------
def heat_yr2day(av_temp, ht_cons_annual):
    """
    Converts annual heat consumption to daily heat consumption, based on daily mean temperatures.
    Underlying algorithm relies on https://www.agcs.at/agcs/clearing/lastprofile/lp_studie2008.pdf
    Implemented consumer clusters are for residential and commercial consumers:
    * HE08 Heizgas Einfamilienhaus LP2008
    * MH08 Heizgas Mehrfamilienhaus LP2008
    * HG08 Heizgas Gewerbe LP2008
    Industry load profiles are specific and typically measured, i.e. not approximated by load profiles

    :param av_temp: datetime-indexed pandas.DataFrame holding daily average temperatures
    :param ht_cons_annual:
    :return:
    """
    # ----------------------------------------------------------------------------
    # fixed parameter: SIGMOID PARAMETERS
    # ----------------------------------------------------------------------------
    sigm_a = {'HE08': 2.8423015098, 'HM08': 2.3994211316, 'HG08': 3.0404658371}
    sigm_b = {'HE08': -36.9902101066, 'HM08': -34.1350545407, 'HG08': -35.6696458089}
    sigm_c = {'HE08': 6.5692076687, 'HM08': 5.6347421440, 'HG08': 5.6585923962}
    sigm_d = {'HE08': 0.1225658254, 'HM08': 0.1728484079, 'HG08': 0.1187586955}

    # ----------------------------------------------------------------------------
    # breakdown of annual consumption to daily consumption
    # ----------------------------------------------------------------------------
    # temperature smoothing
    temp_smooth = pd.DataFrame(index=av_temp.index, columns=['Temp_Sm'])
    for d in av_temp.index:
        if d >= av_temp.first_valid_index() + pd.Timedelta(1, unit='d'):
            temp_smooth.loc[d] = 0.5 * av_temp.loc[d] \
                                 + 0.5 * temp_smooth.loc[d - pd.Timedelta(1, unit='d')]
        else:
            temp_smooth.loc[d] = av_temp.loc[d]

    # determination of normalized daily consumption h_value
    h_value = pd.DataFrame(index=av_temp.index, columns=sigm_a.keys())
    for key in sigm_a:
        h_value[key] = sigm_a[key] / (1 + (sigm_b[key] / (temp_smooth.values - 40)) ** sigm_c[key]) + sigm_d[key]

    # generate matrix of hourly annual consumption
    annual_hourly_consumption = pd.DataFrame(1, index=av_temp.index, columns=sigm_a.keys())
    annual_hourly_consumption = annual_hourly_consumption.set_index(annual_hourly_consumption.index.year, append=True)
    annual_hourly_consumption = annual_hourly_consumption.multiply(ht_cons_annual, level=1).reset_index(drop=True,
                                                                                                        level=1)

    # generate matrix of annual h-value sums
    h_value_annual = h_value.groupby(h_value.index.year).sum()

    # de-normalization of h_value
    cons_daily = h_value.multiply(annual_hourly_consumption)
    cons_daily = cons_daily.set_index(cons_daily.index.year, append=True)
    cons_daily = cons_daily.divide(h_value_annual, level=1).reset_index(drop=True, level=1)

    return cons_daily


def heat_day2hr(df_ht, con_day, con_pattern):
    """
    convert daily heat consumption to hourly heat consumption
    Underlying algorithm relies on https://www.agcs.at/agcs/clearing/lastprofile/lp_studie2008.pdf
    ATTENTION: Algorithm fails for daily average temperatures below -25°C !
    :param df_ht:
    :param con_day:
    :param con_pattern:
    :return:
    """
    sigm_a = {'HE08': 2.8423015098, 'HM08': 2.3994211316, 'HG08': 3.0404658371}
    # apply demand_pattern
    last_day = pd.DataFrame(index=df_ht.tail(1).index + pd.Timedelta(1, unit='d'), columns=sigm_a.keys())

    cons_hourly = con_day.append(last_day).astype(float).resample('1H').sum()
    cons_hourly.drop(cons_hourly.tail(1).index, inplace=True)

    for d in df_ht.index:
        temp_lvl = np.floor(df_ht[d] / 5) * 5
        cons_hlpr = con_day.loc[d] * con_pattern.loc[temp_lvl]
        cons_hlpr = cons_hlpr[cons_hourly.columns]
        cons_hlpr.index = d + pd.to_timedelta(cons_hlpr.index, unit='h')
        cons_hourly.loc[cons_hlpr.index] = cons_hlpr.astype(str).astype(float)

    cons_hourly = cons_hourly.astype(str).astype(float)
    return cons_hourly


def resample_index(index, freq):
    """
    resamples a pandas.DateTimeIndex in daily frequency to
    :param index: pandas.DateTimeIndex to be resampled. Must be daily frequency
    :param freq: pandas frequency string (of higher than daily frequency)
    :return: pandas.DateTimeIndex (resampled)
    """
    assert isinstance(index, pd.DatetimeIndex)
    start_date = index.min()
    end_date = index.max() + pd.DateOffset(days=1)
    resampled_index = pd.date_range(start_date, end_date, freq=freq)[:-1]
    series = pd.Series(resampled_index, resampled_index.floor('D'))
    return pd.DatetimeIndex(series.loc[index].values)


# ======================================================================================================================
# %% functions to retrieve data
# ----------------------------------------------------------------------------------------------------------------------
def download_file(url, save_to):
    """
    downloads a file from a specified url to disk
    :param url: url-string
    :param save_to: destination file name (string)
    :return:
    """
    http = urllib3.PoolManager(ca_certs=certifi.where())
    with http.request('GET', url, preload_content=False) as r, open(save_to, 'wb') as out_file:
        shutil.copyfileobj(r, out_file)


def download_era_temp(filename, year, bounding_box):
    """
    download daily mean temperatures 2m above surface from ERA5 land data from the copernicus climate data store
    requires registration at https://cds.climate.copernicus.eu/user/register
    for further information see: https://confluence.ecmwf.int/display/CKB/ERA5-Land+data+documentation
    :param filename: path and name of downloaded file
    :param year: year for which daily temperature data is downloaded
    :param bounding_box: bounding box of temperature data
    :return:
    """
    logging.info('downloading bounding box=%s for year=%s', bounding_box, year)
    c = cdsapi.Client()

    if os.path.exists(filename):
        logging.info(f'Skipping {filename}, already exists')
        return

    logging.info(f'starting download of {filename}...')
    for i in range(5):
        try:
            c.retrieve(
                'reanalysis-era5-single-levels',
                {
                    'product_type': 'reanalysis',
                    'format': 'netcdf',
                    'variable': '2m_temperature',
                    'year': f'{year}',
                    'month': [f'{month:02d}' for month in range(1, 13, 1)],
                    'area': bounding_box,
                    'day': [f'{day:02d}' for day in range(1, 32)],
                    'time': [f'{hour:02d}:00' for hour in range(24)],
                },
                f'{filename}.part'
            )
        except Exception as e:
            logging.warning('download failed: %s', e)
        else:
            logging.info(f'download of {filename} successful')
            os.rename(f'{filename}.part', filename)
            break
    else:
        logging.warning('download failed permanently')


def download_energy_balance(country, years=range(2012, 2019)):
    # TODO: check if files exist already and download only if not
    if country == 'AT':
        # Austrian energy balance as provided by Statistik Austria
        url = ('http://www.statistik.at/wcm/idc/idcplg?IdcService=GET_NATIVE_FILE&'
               'RevisionSelectionMethod=LatestReleased&dDocName=029955')
        enbal_at = medea_path('data', 'raw', 'enbal_AT.xlsx')
        logging.info(f'downloading Austrian energy balance')
        download_file(url, enbal_at)

    if country == 'DE':
        # German energy balance as provided by AGEB
        ht_enduse_de = pd.DataFrame()
        url_extension_bal = {12: 'xlsx', 13: 'xls', 14: 'xls', 15: 'xlsx', 16: 'xls', 17: 'xlsx', 18: 'xls'}
        url_extension_sat = {12: 'xlsx', 13: 'xls', 14: 'xls', 15: 'xlsx', 16: 'xls', 17: 'xlsx', 18: 'xlsx'}
        for yr in [x - 2000 for x in years]:
            url = 'https://ag-energiebilanzen.de/index.php?article_id=29&'
            url_balance = url + f'fileName=bilanz{yr}d.{url_extension_bal[yr]}'
            url_sat = url + f'fileName=sat{yr}.{url_extension_sat[yr]}'
            enbal_de = medea_path('data', 'raw', f'enbal_DE_20{yr}.{url_extension_bal[yr]}')
            enbal_sat_de = medea_path('data', 'raw', f'enbal_sat_DE_20{yr}.{url_extension_sat[yr]}')
            logging.info(f'downloading German energy balance for year 20{yr}')
            download_file(url_balance, enbal_de)
            download_file(url_sat, enbal_sat_de)


def process_energy_balance(country, years=range(2012, 2019)):
    if country == 'DE':
        url_extension_bal = {12: 'xlsx', 13: 'xls', 14: 'xls', 15: 'xlsx', 16: 'xls', 17: 'xlsx', 18: 'xls'}
        enbal_el = pd.DataFrame()
        for yr in years:
            enbal = pd.read_excel(medea_path('data', 'raw', f'enbal_DE_{yr}.{url_extension_bal[yr - 2000]}'),
                                  sheet_name='tj', index_col=[0], usecols=[0, 29], skiprows=list(range(0, 6)),
                                  nrows=45, na_values=['-'])
            enbal.columns = [yr]
            enbal_el = pd.concat([enbal_el, enbal / 3.6], axis=1)
        enbal_el.to_csv(medea_path('data', 'processed', 'enbal_DE_el.csv'), sep=';')


# ======================================================================================================================
# %% further functions
# ----------------------------------------------------------------------------------------------------------------------
def medea_path(*name):
    """
    creates a path to a folder or file within the medea model
    :param name: one or more strings with folder or file names that are being concatenated in the given order.
    If a file name should be generated, use a name with '.'-extension as last argument
    :return:
    """
    filename = Path(cfg.MEDEA_ROOT_DIR)
    for n in name:
        filename = filename / n
    return filename


def scale_timeseries(time_series, target_sum):
    """
    scales a time series such that its sum is equal to 'target_sum'.
    Typical use is to scale generation time series to match data reported in annual energy balances
    :param time_series: a pd.Series with high-frequency data
    :param annual_sum: a float
    :return: time series scaled to target sum
    """
    scaled_generation = time_series * target_sum / time_series.sum()
    return scaled_generation
