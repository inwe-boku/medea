import logging
import os

import pandas as pd
from gams import *

import config as cfg
from medea.gams_io import df2gdx
from medea.prepare_data import dict_sets, dict_instantiate, static_data, plant_data, ts_data, invest_limits

"""
data_technology, 
data_atc, 
tec_props,
df_itm_invest, 
df_itm_cap,
df_ancil, 
lim_invest_itm, 
lim_invest_thermal, 
lim_invest_atc, 
lim_invest_storage, 
df_feasops, 
storage_clusters,
ts_zonal, 
ts_price, 
ts_inflows
"""
# TODO: Add energy stored in hydro reservoirs - STORAGE_LEVEL

idx = pd.IndexSlice
# --------------------------------------------------------------------------- #
# %% create workspace and database
# --------------------------------------------------------------------------- #
ws = GamsWorkspace(system_directory=cfg.gams_sysdir)
db = ws.add_database()

# --------------------------------------------------------------------------- #
# %% instantiate SETS
# --------------------------------------------------------------------------- #
f_set = df2gdx(db, dict_sets['f'], 'f', 'set', [])
l_set = df2gdx(db, dict_sets['l'], 'l', 'set', [])
prd_set = df2gdx(db, dict_sets['prd'], 'prd', 'set', [])
prop_set = df2gdx(db, dict_sets['props'], 'props', 'set', [])
z_set = df2gdx(db, dict_sets['z'], 'z', 'set', [])
tec_strg_set = df2gdx(db, dict_sets['tec_strg'], 'tec_strg', 'set', [])
tec_itm_set = df2gdx(db, dict_sets['tec_itm'], 'tec_itm', 'set', [])
t_set = df2gdx(db, dict_sets['t'], 't', 'set', [])
tec_set = df2gdx(db, dict_sets['tec'], 'tec', 'set', [])
tec_chp_set = df2gdx(db, pd.DataFrame.from_dict({x: True for x in [y for y in dict_sets['tec'].index if 'chp' in y]},
                                                orient='index'), 'tec_chp', 'set', [])
tec_pth_set = df2gdx(db, pd.DataFrame.from_dict({x: True for x in [y for y in dict_sets['tec'].index if 'pth' in y]},
                                                orient='index'), 'tec_pth', 'set', [])
logging.info('medea sets instantiated')

# --------------------------------------------------------------------------- #
# %% instantiate static PARAMETERS
# --------------------------------------------------------------------------- #

ATC = df2gdx(db, dict_instantiate['atc'].stack(), 'ATC', 'par', [z_set, z_set], '[GW]')
KM = df2gdx(db, dict_instantiate['km'].stack(), 'KM', 'par', [z_set, z_set], '[km]')
EFFICIENCY = df2gdx(db, dict_instantiate['efficiency']['l1'], 'EFFICIENCY', 'par', [tec_set, prd_set, f_set], '[%]')
EMISSION_INTENSITY = df2gdx(db, dict_instantiate['emission_intenstiy'], 'EMISSION_INTENSITY', 'par', [f_set],
                            '[kt CO2 per GWh fuel input]')
FIXED_OM_COST = df2gdx(db, static_data['tec']['om_fix'], 'OM_FIXED_COST', 'par', [tec_set], '[kEUR per GW]')
VARIABLE_OM_COST = df2gdx(db, static_data['tec']['om_var'], 'OM_VARIABLE_COST', 'par', [tec_set], '[kEUR per GWh]')
INVESTCOST_ITM = df2gdx(db, static_data['invest_itm'].stack().reorder_levels([1, 0]).round(4), 'INVESTCOST_ITM', 'par',
                        [z_set, tec_itm_set], '[kEUR per GW]')
INVESTCOST_THERMAL = df2gdx(db, static_data['tec']['annuity'].round(4),
                            'INVESTCOST_THERMAL', 'par', [tec_set], '[kEUR per GW]')
INSTALLED_CAP_ITM = df2gdx(db, dict_instantiate['cap_itm'], 'INSTALLED_CAP_ITM', 'par', [z_set, tec_itm_set], '[GW]')
INSTALLED_CAP_THERM = df2gdx(db, dict_instantiate['tec_props']['cap'], 'INSTALLED_CAP_THERM', 'par',
                             [z_set, tec_set], '[GW]')
NUM = df2gdx(db, dict_instantiate['tec_props']['num'], 'NUM', 'par', [z_set, tec_set], '[#]')

TEC_COUNT = df2gdx(db, dict_instantiate['tec_props']['count'], 'TEC_COUNT', 'par', [z_set, tec_set], '[]')
FEASIBLE_INPUT = df2gdx(db, static_data['feasops']['fuel_need'].round(4), 'FEASIBLE_INPUT', 'par',
                        [tec_set, l_set, f_set], '[GW]')
FEASIBLE_OUTPUT = df2gdx(db, static_data['feasops'][['el', 'ht']].droplevel('fuel_name').stack(), 'FEASIBLE_OUTPUT',
                         'par', [tec_set, l_set, prd_set], '[GW]')
STORAGE_PROPERTIES = df2gdx(db, plant_data['storage_clusters'][dict_sets['props'].index].stack().reorder_levels(
    [1, 0, 2]).round(4), 'STORAGE_PROPERTIES', 'par', [z_set, tec_strg_set, prop_set])
ANCIL_SERVICE_LVL = df2gdx(db, dict_instantiate['ancil'].round(4), 'ANCIL_SERVICE_LVL', 'par', [z_set], '[GW]')
YEAR = df2gdx(db, pd.DataFrame([cfg.year]), 'YEAR', 'par', 0, '[#]')

SWITCH_INVEST_THERM = df2gdx(db, invest_limits['thermal'], 'SWITCH_INVEST_THERM', 'par', 0, 'in {0, inf}')
SWITCH_INVEST_ITM = df2gdx(db, invest_limits['intermittent'].stack(), 'SWITCH_INVEST_ITM', 'par',
                           [z_set, tec_itm_set], 'upper invest limit')
SWITCH_INVEST_STORAGE = df2gdx(db, invest_limits['storage'].stack(), 'SWITCH_INVEST_STORAGE', 'par',
                               [z_set, tec_strg_set], 'upper limit')
SWITCH_INVEST_ATC = df2gdx(db, invest_limits['atc'].stack(), 'SWITCH_INVEST_ATC', 'par',
                           [z_set, z_set], 'upper invest limit')

logging.info('medea parameters instantiated')

# --------------------------------------------------------------------------- #
# %% instantiate dynamic PARAMETERS
# --------------------------------------------------------------------------- #
CONSUMPTION = df2gdx(db, ts_data['zonal'].loc[:, idx[:, :, 'load']].stack((0, 1)).reorder_levels((1, 0, 2)).round(4),
                     'CONSUMPTION', 'par', [z_set, t_set, prd_set])
EXPORT_FLOWS = df2gdx(db, ts_data['zonal'].loc[:, idx[:, 'exports', :]].stack(0).reorder_levels((1, 0)),
                      'FLOW_EXPORT', 'par', [z_set, t_set])
IMPORT_FLOWS = df2gdx(db, ts_data['zonal'].loc[:, idx[:, 'imports', :]].stack(0).reorder_levels((1, 0)),
                      'FLOW_IMPORT', 'par', [z_set, t_set])
GEN_PROFILE = df2gdx(db, ts_data['zonal'].loc[:, idx[:, :, 'profile']].stack((0, 1)).reorder_levels((1, 0, 2)).round(4),
                     'GEN_PROFILE', 'par', [z_set, t_set, tec_itm_set])

PRICE_DA = df2gdx(db, ts_data['price'].loc[:, idx['price_day_ahead', :]].stack(), 'PRICE_DA', 'par', [t_set, z_set])
PRICE_CO2 = df2gdx(db, ts_data['price'].loc[:, idx['EUA', :]].stack(), 'PRICE_CO2', 'par', [t_set, z_set])
PRICE_FUEL = df2gdx(db, ts_data['price'].drop(['EUA', 'price_day_ahead'], axis=1).stack((0, 1)).reorder_levels(
    (0, 2, 1)).round(4), 'PRICE_FUEL', 'par', [t_set, z_set, f_set])

RESERVOIR_INFLOWS = df2gdx(db, ts_data['inflows'].stack((0, 1)).reorder_levels((1, 0, 2)).astype('float').round(4),
                           'RESERVOIR_INFLOWS', 'par', [z_set, t_set, tec_strg_set])
# STORAGE_LEVEL = df2gdx(db, df_storage_lvl, 'STORAGE_LEVEL', 'par', [r_set, t_set])
# NUM_AVAILABLE = df2gdx(db, df_num_avail, 'NUM_AVAILABLE', 'par', [r_set, t_set, tec_set])

logging.info('medea`s timeseries instantiated')

# --------------------------------------------------------------------------- #
# %% data export to gdx
# --------------------------------------------------------------------------- #
export_location = os.path.join(cfg.folder, 'medea', 'data', 'medea_main_data.gdx')
db.export(export_location)
logging.info(f'medea gdx exported to {export_location}')
