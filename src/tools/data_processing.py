import ftplib
import shutil

import numpy as np
import pandas as pd
import urllib3


# ==============================================================================================
# general functions

def is_leapyear(year):
    """Determine whether a given year is a leapyear"""
    flag = year % 400 == 0 or (year % 4 == 0 and year % 100 != 0)
    return flag


def hours_in_year(year):
    if is_leapyear(year):
        return 8784
    else:
        return 8760


# ==============================================================================================
# functions for heat load calculation
# ----------------------------------------------------------------------------------------------
"""
for a description of the algorithm see: https://www.agcs.at/agcs/clearing/lastprofile/lp_studie2008.pdf

Implemented consumer clusters are for residential and commercial consumers:
    HE08 Heizgas Einfamilienhaus LP2008
    MH08 Heizgas Mehrfamilienhaus LP2008
    HG08 Heizgas Gewerbe LP2008

industry load profiles are specific and typically measured, i.e. not approximated by load profiles 
"""


# ----------------------------------------------------------------------------------------------


def heat_yr2day(av_temp, ht_cons_annual):
    """
    expected inputs:
    av_temp ... pandas Series with datetime-index holding daily average temperatures
    ht_cons_annual ... pandas dataframe with
    :param av_temp:
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
    # ----------------------------------------------------------------------------
    # breakdown of daily consumption to hourly consumption
    # FAILS FOR DAILY AVERAGE TEMPERATURES BELOW -25°C
    # ----------------------------------------------------------------------------
    sigm_a = {'HE08': 2.8423015098, 'HM08': 2.3994211316, 'HG08': 3.0404658371}
    # apply gas_demand_pattern
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
    """Resamples each day in the daily `index` to the specified `freq`.
    Parameters
    ----------
    index : pd.DatetimeIndex
        The daily-frequency index to resample
    freq : str
        A pandas frequency string which should be higher than daily
    Returns
    -------
    pd.DatetimeIndex
        The resampled index
    """
    assert isinstance(index, pd.DatetimeIndex)
    start_date = index.min()
    end_date = index.max() + pd.DateOffset(days=1)
    resampled_index = pd.date_range(start_date, end_date, freq=freq)[:-1]
    series = pd.Series(resampled_index, resampled_index.floor('D'))
    return pd.DatetimeIndex(series.loc[index].values)


# ================================================================================


def download_file(url, save_to):
    http = urllib3.PoolManager()
    with http.request('GET', url, preload_content=False) as r, open(save_to, 'wb') as out_file:
        shutil.copyfileobj(r, out_file)


pwd = 'ausmaus76'


def get_from_entsoe_ftp(user, pwd):
    ftp = ftplib.FTP('sftp-transparency.entsoe.eu')
    ftp.login(user, pwd)
    data = []
    ftp.dir(data.append)
    ftp.quit()

    for line in data:
        print
        "-", line
