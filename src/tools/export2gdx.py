import logging
import os

import pandas as pd
from gams import *

import config as cfg
from src.tools.gams_io import df2gdx
from src.tools.preprocess_data import dict_sets, plant_data, ts_data, estimates, invest_limits

idx = pd.IndexSlice
# --------------------------------------------------------------------------- #
# %% create workspace and database
# --------------------------------------------------------------------------- #
ws = GamsWorkspace(system_directory=cfg.GMS_SYS_DIR)
db = ws.add_database()

# --------------------------------------------------------------------------- #
# %% instantiate SETS
# --------------------------------------------------------------------------- #
all_set = df2gdx(db, dict_sets['all_tec'], 'all_tec', 'set', [])
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
# %% selectors
# --------------------------------------------------------------------------- #
intermittent = plant_data['technology'].loc[plant_data['technology']['intermittent'] == 1].index
storage = plant_data['technology'].loc[plant_data['technology']['storage'] == 1].index
dispatchable = plant_data['technology'].loc[plant_data['technology']['conventional'] == 1].index
transmission = plant_data['technology'].loc[plant_data['technology']['transmission'] == 1].index

# --------------------------------------------------------------------------- #
# %% instantiate static PARAMETERS
# --------------------------------------------------------------------------- #

# technology parameters
# TODO: consider reformulating model to have one capital cost / O&M parameter for all technologies
CAPITALCOST_P = df2gdx(db, plant_data['technology'].loc[:, 'capex_p'],
                       'CAPITALCOST_P', 'par', [all_set], '[kEUR per GW]')
CAPITALCOST_E = df2gdx(db, plant_data['technology'].loc[:, 'capex_e'],
                       'CAPITALCOST_E', 'par', [all_set], '[kEUR per GW]')
LIFETIME = df2gdx(db, plant_data['technology'].loc[:, 'lifetime'],
                  'LIFETIME', 'par', [all_set], '[a]')
DISCOUNT_RATE = df2gdx(db, estimates['DISCOUNT_RATE'], 'DISCOUNT_RATE', 'par', [z_set], '[]')

EFFICIENCY_G = df2gdx(db, plant_data['technology'].loc[dispatchable, ['eta_ec', 'primary_product', 'fuel']].set_index(
    ['primary_product', 'fuel'], append=True),
                      'EFFICIENCY_G', 'par', [i_set, m_set, f_set], '[%]')
EFFICIENCY_S_OUT = df2gdx(db, plant_data['technology'].loc[storage, 'eta_ec'],
                          'EFFICIENCY_S_OUT', 'par', [k_set], '[GW]')

EFFICIENCY_S_IN = df2gdx(db, plant_data['technology'].loc[storage, 'eta_ec'],
                         'EFFICIENCY_S_IN', 'par', [k_set], '[GW]')

OM_COST_G_QFIX = df2gdx(db, plant_data['technology'].loc[dispatchable, 'opex_f'],
                        'OM_COST_G_QFIX', 'par', [i_set], '[kEUR per GW]')
OM_COST_G_VAR = df2gdx(db, plant_data['technology'].loc[dispatchable, 'opex_v'],
                       'OM_COST_G_VAR', 'par', [i_set], '[kEUR per GWh]')
OM_COST_R_QFIX = df2gdx(db, plant_data['technology'].loc[intermittent, 'opex_f'],
                        'OM_COST_R_QFIX', 'par', [n_set], '[kEUR per GW]')
OM_COST_R_VAR = df2gdx(db, plant_data['technology'].loc[intermittent, 'opex_v'],
                       'OM_COST_R_VAR', 'par', [n_set], '[kEUR per GWh]')

FEASIBLE_INPUT = df2gdx(db, plant_data['chp']['fuel_need'],
                        'FEASIBLE_INPUT', 'par', [i_set, l_set, f_set], '[GW]')
FEASIBLE_OUTPUT = df2gdx(db, plant_data['chp'][['el', 'ht']].droplevel('f').stack(),
                         'FEASIBLE_OUTPUT', 'par', [i_set, l_set, m_set], '[GW]')

# initial capacity endowment
INITIAL_CAP_G = df2gdx(db, plant_data['installed'].loc[
    idx['Installed Capacity Out', :, cfg.year]].stack().loc[idx[:, dispatchable]],
                       'INITIAL_CAP_G', 'par', [z_set, i_set], '[GW]')
INITIAL_CAP_R = df2gdx(db, plant_data['installed'].loc[
    idx['Installed Capacity Out', :, cfg.year]].stack().loc[idx[:, intermittent]],
                       'INITIAL_CAP_R', 'par', [z_set, n_set], '[GW]')
INITIAL_CAP_S_OUT = df2gdx(db, plant_data['installed'].loc[
    idx['Installed Capacity Out', :, cfg.year]].stack().loc[idx[:, storage]],
                           'INITIAL_CAP_S_OUT', 'par', [z_set, k_set], '[GW]')
INITIAL_CAP_S_IN = df2gdx(db, plant_data['installed'].loc[
    idx['Installed Capacity In', :, cfg.year]].stack().loc[idx[:, storage]],
                          'INITIAL_CAP_S_IN', 'par', [z_set, k_set], '[GW]')
INITIAL_CAP_V = df2gdx(db, plant_data['installed'].loc[
    idx['Storage Capacity', :, cfg.year]].stack().loc[idx[:, storage]],
                       'INITIAL_CAP_V', 'par', [z_set, k_set], '[GW]')
INITIAL_CAP_X = df2gdx(db, plant_data['CAP_X'].stack(),
                       'INITIAL_CAP_X', 'par', [z_set, z_set], '[GW]')
DISTANCE = df2gdx(db, plant_data['DISTANCE'].stack(),
                  'DISTANCE', 'par', [z_set, z_set], '[km]')

# further parameters
PEAK_LOAD = df2gdx(db, ts_data['PEAK_LOAD'], 'PEAK_LOAD', 'par', [z_set], '[GW]')
PEAK_PROFILE = df2gdx(db, ts_data['PEAK_PROFILE'], 'PEAK_PROFILE', 'par', [z_set, n_set], '[]')
# TODO: Document values of LAMBDA and SIGMA
LAMBDA = df2gdx(db, estimates['ESTIMATES'].loc['LAMBDA', :], 'LAMBDA', 'par', [z_set], '[]')
SIGMA = df2gdx(db, estimates['ESTIMATES'].loc['SIGMA', :], 'SIGMA', 'par', [z_set], '[]')
VALUE_NSE = df2gdx(db, estimates['ESTIMATES'].loc['VALUE_NSE'], 'VALUE_NSE', 'par', [z_set], 'EUR per MWh')

CO2_INTENSITY = df2gdx(db, estimates['CO2_INTENSITY'],
                       'CO2_INTENSITY', 'par', [f_set], '[kt CO2 per GWh fuel input]')

AIR_POL_COST_FIX = df2gdx(db, estimates['AIR_POLLUTION']['fixed cost'],
                          'AIR_POL_COST_FIX', 'par', [f_set], 'EUR per MW')
AIR_POL_COST_VAR = df2gdx(db, estimates['AIR_POLLUTION']['variable cost'],
                          'AIR_POL_COST_VAR', 'par', [f_set], 'EUR per MWh')

# TODO: Add first-period energy content of storage - STORAGE_LEVEL
# --------------------------------------------------------------------------- #
# time series
# --------------------------------------------------------------------------- #

DEMAND = df2gdx(db, ts_data['ZONAL'].loc[:, idx[:, :, 'load']].stack((0, 1)).reorder_levels((1, 0, 2)).round(4),
                'DEMAND', 'par', [z_set, t_set, m_set])
GEN_PROFILE = df2gdx(db, ts_data['ZONAL'].loc[:, idx[:, :, 'profile']].stack((0, 1)).reorder_levels((1, 0, 2)).round(4),
                     'GEN_PROFILE', 'par', [z_set, t_set, n_set])
INFLOWS = df2gdx(db, ts_data['INFLOWS'].stack((0, 1)).reorder_levels((1, 0, 2)).astype('float').round(4),
                 'INFLOWS', 'par', [z_set, t_set, k_set])

PRICE_CO2 = df2gdx(db, ts_data['price'].loc[:, idx['EUA', :]].stack().reorder_levels((1, 0)),
                   'PRICE_CO2', 'par', [z_set, t_set])
PRICE_FUEL = df2gdx(db, ts_data['price'].drop(['EUA', 'price_day_ahead'], axis=1).stack((0, 1)).reorder_levels(
    (2, 0, 1)).round(4), 'PRICE_FUEL', 'par', [z_set, t_set, f_set])
# PRICE_DA is NOT required by model
PRICE_DA = df2gdx(db, ts_data['price'].loc[:, idx['price_day_ahead', :]].stack(), 'PRICE_DA', 'par', [t_set, z_set])

# --------------------------------------------------------------------------- #
# ancillary parameters
# --------------------------------------------------------------------------- #
YEAR = df2gdx(db, pd.DataFrame([cfg.year]), 'YEAR', 'par', 0, '[#]')

SWITCH_INVEST_THERM = df2gdx(db, invest_limits['thermal'],
                             'SWITCH_INVEST_THERM', 'par', 0, 'in {0, inf}')
SWITCH_INVEST_ITM = df2gdx(db, invest_limits['intermittent'].stack(),
                           'SWITCH_INVEST_ITM', 'par', [z_set, n_set], 'upper invest limit')
SWITCH_INVEST_STORAGE = df2gdx(db, invest_limits['storage'].stack(),
                               'SWITCH_INVEST_STORAGE', 'par', [z_set, k_set], 'upper limit')
SWITCH_INVEST_ATC = df2gdx(db, invest_limits['atc'].stack(),
                           'SWITCH_INVEST_ATC', 'par', [z_set, z_set], 'upper invest limit')

logging.info('medea data exported')

# --------------------------------------------------------------------------- #
# %% data export to gdx
# --------------------------------------------------------------------------- #
export_location = os.path.join(cfg.MEDEA_ROOT_DIR, 'data', 'gdx', 'medea_main_data_adj.gdx')
db.export(export_location)
logging.info(f'medea gdx exported to {export_location}')
