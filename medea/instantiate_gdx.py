import logging
import os

import pandas as pd
from gams import *

import config as cfg
from medea.gams_io import df2gdx
from medea.prepare_data import dict_sets, dict_instantiate, static_data, plant_data, ts_data, invest_limits

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
m_set = df2gdx(db, dict_sets['m'], 'm', 'set', [])
z_set = df2gdx(db, dict_sets['z'], 'z', 'set', [])
k_set = df2gdx(db, dict_sets['k'], 'k', 'set', [])
n_set = df2gdx(db, dict_sets['n'], 'n', 'set', [])
t_set = df2gdx(db, dict_sets['t'], 't', 'set', [])
i_set = df2gdx(db, dict_sets['i'], 'i', 'set', [])
j_set = df2gdx(db, pd.DataFrame.from_dict({x: True for x in [y for y in dict_sets['i'].index if 'chp' in y]},
                                          orient='index'), 'j', 'set', [])
h_set = df2gdx(db, pd.DataFrame.from_dict({x: True for x in [y for y in dict_sets['i'].index if 'pth' in y]},
                                          orient='index'), 'h', 'set', [])
logging.info('medea sets instantiated')

# --------------------------------------------------------------------------- #
# %% instantiate static PARAMETERS
# --------------------------------------------------------------------------- #
CAPITALCOST_G = df2gdx(db, static_data['tec']['annuity'].round(4),
                            'CAPITALCOST_G', 'par', [i_set], '[kEUR per GW]')
CAPITALCOST_R = df2gdx(db, static_data['CAPCOST_R'].stack().reorder_levels([1, 0]).round(4), 'CAPITALCOST_R', 'par',
                       [z_set, n_set], '[kEUR per GW]')
CAPITALCOST_S = df2gdx(db, plant_data['storage_clusters']['cost_power'].reorder_levels((1, 0)), 'CAPITALCOST_S', 'par',
                       [z_set, k_set], '[GW]')
CAPITALCOST_V = df2gdx(db, plant_data['storage_clusters']['cost_energy'].reorder_levels((1, 0)), 'CAPITALCOST_V', 'par',
                       [z_set, k_set], '[GW]')
CAPITALCOST_X = df2gdx(db, static_data['CAPCOST_X'], 'CAPITALCOST_X', 'par', [z_set], 'kEUR per GW')
CO2_INTENSITY = df2gdx(db, dict_instantiate['CO2_INTENSITY'], 'CO2_INTENSITY', 'par', [f_set],
                       '[kt CO2 per GWh fuel input]')
DEMAND = df2gdx(db, ts_data['zonal'].loc[:, idx[:, :, 'load']].stack((0, 1)).reorder_levels((1, 0, 2)).round(4),
                'DEMAND', 'par', [z_set, t_set, m_set])
DISTANCE = df2gdx(db, dict_instantiate['DISTANCE'].stack(), 'DISTANCE', 'par', [z_set, z_set], '[km]')
EFFICIENCY_G = df2gdx(db, dict_instantiate['efficiency']['l1'], 'EFFICIENCY_G', 'par', [i_set, m_set, f_set], '[%]')

EFFICIENCY_S_OUT = df2gdx(db, plant_data['storage_clusters']['efficiency_out'].reorder_levels((1, 0)),
                          'EFFICIENCY_S_OUT', 'par', [z_set, k_set], '[GW]')
EFFICIENCY_S_IN = df2gdx(db, plant_data['storage_clusters']['efficiency_in'].reorder_levels((1, 0)), 'EFFICIENCY_S_IN',
                         'par', [z_set, k_set], '[GW]')
FEASIBLE_INPUT = df2gdx(db, static_data['feasops']['fuel_need'].round(4), 'FEASIBLE_INPUT', 'par',
                        [i_set, l_set, f_set], '[GW]')
FEASIBLE_OUTPUT = df2gdx(db, static_data['feasops'][['el', 'ht']].droplevel('fuel_name').stack(), 'FEASIBLE_OUTPUT',
                         'par', [i_set, l_set, m_set], '[GW]')
GEN_PROFILE = df2gdx(db, ts_data['zonal'].loc[:, idx[:, :, 'profile']].stack((0, 1)).reorder_levels((1, 0, 2)).round(4),
                     'GEN_PROFILE', 'par', [z_set, t_set, n_set])
INFLOWS = df2gdx(db, ts_data['inflows'].stack((0, 1)).reorder_levels((1, 0, 2)).astype('float').round(4),
                 'INFLOWS', 'par', [z_set, t_set, k_set])
INITIAL_CAP_G = df2gdx(db, dict_instantiate['tec_props']['cap'], 'INITIAL_CAP_G', 'par',
                       [z_set, i_set], '[GW]')
INITIAL_CAP_R = df2gdx(db, dict_instantiate['CAP_R'], 'INITIAL_CAP_R', 'par', [z_set, n_set], '[GW]')
INITIAL_CAP_S_OUT = df2gdx(db, plant_data['storage_clusters']['power_out'].reorder_levels((1, 0)), 'INITIAL_CAP_S_OUT',
                           'par', [z_set, k_set], '[GW]')
INITIAL_CAP_S_IN = df2gdx(db, plant_data['storage_clusters']['power_in'].reorder_levels((1, 0)), 'INITIAL_CAP_S_IN',
                          'par', [z_set, k_set], '[GW]')
INITIAL_CAP_V = df2gdx(db, plant_data['storage_clusters']['energy_max'].reorder_levels((1, 0)), 'INITIAL_CAP_V', 'par',
                           [z_set, k_set], '[GW]')
INITIAL_CAP_X = df2gdx(db, dict_instantiate['CAP_X'].stack(), 'INITIAL_CAP_X', 'par', [z_set, z_set], '[GW]')

# TODO: Estimate LAMBDA, i.e. the share of must-run capacity in conventional capacity (controlling for renewables capacity)
LAMBDA = df2gdx(db, static_data['LAMBDA'], 'LAMBDA', 'par', 0, '[]')

OM_COST_QFIX = df2gdx(db, static_data['tec']['om_fix'], 'OM_COST_QFIX', 'par', [i_set], '[kEUR per GW]')
OM_COST_VAR = df2gdx(db, static_data['tec']['om_var'], 'OM_COST_VAR', 'par', [i_set], '[kEUR per GWh]')

PEAK_LOAD = df2gdx(db, dict_instantiate['PEAK_LOAD'], 'PEAK_LOAD', 'par', [z_set], '[GW]')
PEAK_PROFILE = df2gdx(db, dict_instantiate['PEAK_PROFILE'], 'PEAK_PROFILE', 'par', [z_set, n_set], '[]')

PRICE_CO2 = df2gdx(db, ts_data['price'].loc[:, idx['EUA', :]].stack(), 'PRICE_CO2', 'par', [t_set, z_set])
PRICE_FUEL = df2gdx(db, ts_data['price'].drop(['EUA', 'price_day_ahead'], axis=1).stack((0, 1)).reorder_levels(
    (0, 2, 1)).round(4), 'PRICE_FUEL', 'par', [t_set, z_set, f_set])
# PRICE_DA is NOT required by model
PRICE_DA = df2gdx(db, ts_data['price'].loc[:, idx['price_day_ahead', :]].stack(), 'PRICE_DA', 'par', [t_set, z_set])

SIGMA = df2gdx(db, static_data['SIGMA'], 'SIGMA', 'par', 0, '[]')

VALUE_NSE = df2gdx(db, static_data['VALUE_NSE'], 'VALUE_NSE', 'par', [z_set], 'EUR per MWh')

# potentially useful for unit committment-models
# NUM = df2gdx(db, dict_instantiate['tec_props']['num'], 'NUM', 'par', [z_set, i_set], '[#]')
# TEC_COUNT = df2gdx(db, dict_instantiate['tec_props']['count'], 'TEC_COUNT', 'par', [z_set, i_set], '[]')

# STORAGE_PROPERTIES = df2gdx(db, plant_data['storage_clusters'][dict_sets['props'].index].reorder_levels([1, 0]).round(4), 'STORAGE_PROPERTIES', 'par', [z_set, k_set, prop_set])

# ANCIL_SERVICE_LVL = df2gdx(db, dict_instantiate['ancil'].round(4), 'ANCIL_SERVICE_LVL', 'par', [z_set], '[GW]')

YEAR = df2gdx(db, pd.DataFrame([cfg.year]), 'YEAR', 'par', 0, '[#]')

SWITCH_INVEST_THERM = df2gdx(db, invest_limits['thermal'], 'SWITCH_INVEST_THERM', 'par', 0, 'in {0, inf}')
SWITCH_INVEST_ITM = df2gdx(db, invest_limits['intermittent'].stack(), 'SWITCH_INVEST_ITM', 'par',
                           [z_set, n_set], 'upper invest limit')
SWITCH_INVEST_STORAGE = df2gdx(db, invest_limits['storage'].stack(), 'SWITCH_INVEST_STORAGE', 'par',
                               [z_set, k_set], 'upper limit')
SWITCH_INVEST_ATC = df2gdx(db, invest_limits['atc'].stack(), 'SWITCH_INVEST_ATC', 'par',
                           [z_set, z_set], 'upper invest limit')

logging.info('medea parameters instantiated')

# --------------------------------------------------------------------------- #
# %% instantiate dynamic PARAMETERS
# --------------------------------------------------------------------------- #

# EXPORT_FLOWS = df2gdx(db, ts_data['zonal'].loc[:, idx[:, 'exports', :]].stack(0).reorder_levels((1, 0)),
#                       'FLOW_EXPORT', 'par', [z_set, t_set])
# IMPORT_FLOWS = df2gdx(db, ts_data['zonal'].loc[:, idx[:, 'imports', :]].stack(0).reorder_levels((1, 0)),
#                       'FLOW_IMPORT', 'par', [z_set, t_set])
# STORAGE_LEVEL = df2gdx(db, df_storage_lvl, 'STORAGE_LEVEL', 'par', [r_set, t_set])
# NUM_AVAILABLE = df2gdx(db, df_num_avail, 'NUM_AVAILABLE', 'par', [r_set, t_set, i_set])

logging.info('medea`s timeseries instantiated')

# --------------------------------------------------------------------------- #
# %% data export to gdx
# --------------------------------------------------------------------------- #
export_location = os.path.join(cfg.folder, 'medea', 'data', 'medea_main_data_consistent.gdx')
db.export(export_location)
logging.info(f'medea gdx exported to {export_location}')
