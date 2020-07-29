import os

import pandas as pd
from gams import *
from scipy.stats import pearsonr

import config as cfg
from src.tools.gams_io import gdx2df

idx = pd.IndexSlice

res = pd.read_csv(os.path.join(cfg.MEDEA_ROOT_DIR, 'projects', 'asparagus', 'results', 'results.csv'))

# %% analyze correlation of hourly imports / exports with generation profiles of intermittents
# read intermittent generation profiles
ws = GamsWorkspace(system_directory=cfg.GMS_SYS_DIR)
TS_FILE = os.path.join(cfg.MEDEA_ROOT_DIR, 'data', 'processed', 'medea_regional_timeseries.csv')
ts = pd.read_csv(TS_FILE)
ts['DateTime'] = pd.to_datetime(ts['DateTime'])
ts.set_index('DateTime', inplace=True)
# constrain data to scenario year
ts = ts.loc[(pd.Timestamp(cfg.year, 1, 1, 0, 0).tz_localize('UTC') <= ts.index) &
            (ts.index <= pd.Timestamp(cfg.year, 12, 31, 23, 0).tz_localize('UTC'))]

# read hourly net imports from gdx output
identifier = f'asparagus_h2stack_30_16_36715'
FNAME = os.path.join('C:/Users', 'Sebastian', 'asparagus_gdx', f'medea_out_{identifier}.gdx')
db_output = ws.add_database_from_gdx(FNAME)
df = gdx2df(db_output, 'x', ['t'], ['z', 'zz'])
df.index = ts.index

nx_at = pd.DataFrame(data=0.0, index=df.index, columns=['X', 'I', 'pv_de', 'wind_at', 'load_at'])
nx_at.loc[df.loc[:, idx['AT', 'DE']] > 0, 'X'] = df.loc[df.loc[:, idx['AT', 'DE']] > 0, idx['AT', 'DE']]
nx_at.loc[df.loc[:, idx['AT', 'DE']] < 0, 'I'] = - df.loc[df.loc[:, idx['AT', 'DE']] < 0, idx['AT', 'DE']]
nx_at.index = ts.index

nx_at.loc[:, 'pv_de'] = ts.loc[:, 'DE-pv-profile']
nx_at.loc[:, 'pv_at'] = ts.loc[:, 'AT-pv-profile']
nx_at.loc[:, 'wind_at'] = ts.loc[:, 'AT-wind_on-profile']
nx_at.loc[:, 'load_at'] = ts.loc[:, 'AT-power-load']
nx_at.loc[:, 'ror_at'] = ts.loc[:, 'AT-ror-profile']
nx_at.loc[:, 'rorg_at'] = ts.loc[:, 'AT-ror-profile'] * ts.loc[:, 'AT-ror-capacity']

pearsonr(nx_at['pv_at'].values, nx_at['I'].values)
pearsonr(nx_at['wind_at'].values, nx_at['X'].values)

# monthly values
mx_at = nx_at.resample('M').mean()

mx_at['rel_X'] = mx_at['X'] / (mx_at['load_at'] - mx_at['rorg_at'])
mx_at['rel_I'] = mx_at['I'] / (mx_at['load_at'] - mx_at['rorg_at'])
