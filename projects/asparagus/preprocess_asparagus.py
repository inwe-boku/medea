# %% imports
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy.signal import savgol_filter

import config as cfg
from src.tools.data_processing import medea_path

# %% settings
FNAME = medea_path('data', 'processed', 'medea_regional_timeseries.csv')

# %% read data
df = pd.read_csv(FNAME, index_col=[0])
df.index = pd.to_datetime(df.index)
cols = ['AT-pv-profile', 'AT-wind_on-profile', 'AT-ror-profile']
dfs = df.loc[str(cfg.year), cols]

# %% extract trend from hourly time series of PV and wind
trend = pd.DataFrame(data=np.nan, columns=cols, index=dfs.index)
detrend = pd.DataFrame(data=np.nan, columns=cols, index=dfs.index)
savgol_parameter = pd.DataFrame(columns=cols, index=['window_length', 'poly_order'])
savgol_parameter.loc['poly_order', :] = 3
savgol_parameter.loc['window_length', 'AT-pv-profile'] = 673
savgol_parameter.loc['window_length', 'AT-wind_on-profile'] = 1161
savgol_parameter.loc['window_length', 'AT-ror-profile'] = 561

for i in [cols[0]]:
    trend[i] = savgol_filter(dfs[i], savgol_parameter.loc['window_length', i], savgol_parameter.loc['poly_order', i])
    detrend[i] = dfs[i] / trend[i] * dfs[i].mean()
    detrend[i].plot()
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
