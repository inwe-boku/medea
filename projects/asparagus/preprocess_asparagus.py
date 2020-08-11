# %% imports

import matplotlib.pyplot as plt
import pandas as pd
from scipy.signal import savgol_filter
from statsmodels.tsa.seasonal import STL

import config as cfg
from src.tools.data_processing import medea_path

# %% settings
FNAME = medea_path('data', 'processed', 'medea_regional_timeseries.csv')


# %% define functions
def seasonal_decomposition(time_series, resample_window='D', window_length=73, poly_order=3):
    # TODO: check if timeseries has DateTimeIndex. Throw error if not.
    # TODO: check if timeseries is a single column
    df_sdc = pd.DataFrame(columns=['seasonal', 'day', 'residual', 'deseas_abs', 'deseas_rel'])
    df_sdc['day'] = time_series.resample(resample_window).sum()
    df_sdc['seasonal'] = savgol_filter(df_sdc['day'], window_length, poly_order)
    df_sdc['residual'] = df_sdc['day'] - df_sdc['seasonal']
    df_sdc['deseas_abs'] = df_sdc['residual'] + df_sdc['day'].mean()
    df_sdc['deseas_rel'] = (1 + df_sdc['residual'] / df_sdc['seasonal']) * df_sdc['day'].mean()
    return df_sdc


def extract_hourly_pattern(time_series):
    # TODO: check if timeseries has DateTimeIndex. Throw error if not.
    # TODO: check if timeseries is a single column
    df = time_series.groupby(time_series.index.hour).mean() / time_series.groupby(time_series.index.hour).mean().sum()
    return df


def extract_monthly_pattern(time_series):
    df = time_series.groupby(time_series.index.month).mean() / time_series.groupby(time_series.index.month).mean().sum()
    return df


def apply_pattern(aggregate_series, pattern):
    lst = [i * aggregate_series.iloc[d] for d in range(0, len(aggregate_series)) for i in list(pattern)]
    df = pd.DataFrame(lst, columns=['Values'])
    return df


# %% process data
df = pd.read_csv(FNAME, index_col=[0])
df.index = pd.to_datetime(df.index)

cols = ['AT-power-load', 'AT-pv-generation', 'AT-pv-capacity', 'AT-wind_on-generation', 'AT-wind_on-capacity',
        'AT-ror-profile']
dfs = df.loc[str(cfg.year), cols]
# dfs = df.loc[(df.index.year >= 2015) & (df.index.year <= 2018), cols]

# scale generation of PV to levels consistent with national energy balance
pv_profile = dfs['AT-pv-generation'] * 1.167 / dfs['AT-pv-capacity']

# scale generation of onshore wind to levels consistent with national energy balance
wind_profile = dfs['AT-wind_on-generation'] * 0.983 / dfs['AT-wind_on-capacity']

# scale run-of-river profile to levels consistent with e-control Betriebsstatistik BStGes-JR1_Bilanz.xlsx available from
# https://www.e-control.at/documents/1785851/1811609/BStGes-JR1_Bilanz.xlsx
ror_profile = dfs['AT-ror-profile'] * 1.038

# %% LOESS filter for additive decomposition

# (1) decomposition of PV profile
pv_loess = STL(pv_profile, seasonal=49, trend=673)
pv_fit = pv_loess.fit()

# (2) decomposition of Wind Onshore profile
wind_loess = STL(wind_profile, seasonal=673, trend=2161)
wind_fit = wind_loess.fit()

# generate synthetic profiles
synthetic = pd.DataFrame(index=wind_profile.index, columns=['pv_noseas', 'wind_noseas', 'wind_pvpat', 'pv_windpat'])

synthetic['pv_noseas'] = pv_fit.seasonal + pv_fit.resid + pv_fit.trend.mean()

synthetic.loc['2016-01', 'pv_noseas'].plot()
plt.show()

# %% get seasonal patterns of wind, pv, load in Austria
seasonal_pattern = pd.DataFrame(columns=cols)
deseasonalized = pd.DataFrame(columns=cols)
for c in dfs.columns:
    sdc = seasonal_decomposition(dfs.loc[:, c], resample_window='W', window_length=9, poly_order=1)
    seasonal_pattern[c] = sdc['seasonal']
    deseasonalized[c] = sdc['deseas_rel']

(seasonal_pattern / seasonal_pattern.mean()).plot()
plt.show()

# %% what do i want to say?
# difference in system cost comes from
# (1) differences in capital cost and annual energy generation
# (2) differences in the time of generation \footnote{and the location of generation, though we do not consider that here}
#     notably in seasonal patterns over a year and short-term patterns within a day, both systematic and seemingly random.

# create pv pattern with full-load hours leading to equivalent LCOE --> observe if wind or solar installed

# create pv pattern with seasonal variation, but no hourly variations
# --> compare marginal -> value of seasonal fluctuations // also look at correlations of seasonal patterns
# create pv pattern with hourly variation (by season?), but no daily variations
# --> value of hourly variation // also look at correlation of hourly patterns
# create pv pattern with random variation only ---> how?
# --> value of randomness
