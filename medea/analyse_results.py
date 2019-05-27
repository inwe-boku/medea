import os

from gams import *

import config as cfg
from medea.gams_wrappers import gdx2df

# df = pd.read_csv(os.path.join(cfg.folder, 'medea', 'opt'))
run_string = 'PoBu_EUA20_curt_htpmp_1'

ws = GamsWorkspace(system_directory=cfg.gams_sysdir)
filename = f'medea_out_{run_string}.gdx'
db_output = ws.add_database_from_gdx(os.path.join(cfg.folder, 'medea', 'opt', filename))

read_variables = {
   'q_curtail': (['t'], ['r', 'prd']),
    'flow': (['t'], ['r', 'rr']),
    'invest_res': (['tec_itm'], ['r']),
    'GEN_PROFILE': (['t'], ['r', 'tec_itm']),
    'CONSUMPTION': (['t'], ['r', 'prd']),
    'INSTALLED_CAP_ITM': (['tec_itm'], ['r'])
        # 'ntc_invest': (['r'], ['r'])
    }
result_dict = {key: gdx2df(db_output, key, value[0], value[1])
               for key, value in read_variables.items()}

# #% data analysis

df_windat = result_dict['GEN_PROFILE'].loc[:, ('AT', 'wind_on')] * (
    result_dict['invest_res'].loc['wind_on', 'AT'] + result_dict['INSTALLED_CAP_ITM'].loc['wind_on', 'AT'])
df_pvat = result_dict['GEN_PROFILE'].loc[:, ('AT', 'pv')] * (
    result_dict['invest_res'].loc['pv', 'AT'] + result_dict['INSTALLED_CAP_ITM'].loc['pv', 'AT'])
df_rorat = result_dict['GEN_PROFILE'].loc[:, ('AT', 'ror')] * (
    result_dict['invest_res'].loc['ror', 'AT'] + result_dict['INSTALLED_CAP_ITM'].loc['ror', 'AT'])
df_itm = df_windat + df_pvat
df_consat = result_dict['CONSUMPTION'].loc[:, ('AT', 'Power')]
df_curt = result_dict['q_curtail'].loc[:, ('AT', 'Power')]

df_surpat = df_windat + df_pvat + df_rorat - df_consat
df_surpat_pos = df_surpat.copy()
df_surpat_pos.loc[df_surpat_pos < 0] = 0

df_surpat.corr(df_curt)
df_surpat_pos.corr(df_curt)

