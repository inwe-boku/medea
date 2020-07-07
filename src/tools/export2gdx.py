import logging
import os

import pandas as pd
from gams import *

import config as cfg
from src.tools.gams_io import df2gdx
from src.tools.preprocess_data import dict_sets, plant_data, ts_data

# TODO: Add energy stored in hydro reservoirs - STORAGE_LEVEL

idx = pd.IndexSlice
# --------------------------------------------------------------------------- #
# %% create workspace and database
# --------------------------------------------------------------------------- #
ws = GamsWorkspace(system_directory=cfg.GMS_SYS_DIR)
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
# %% selectors
# --------------------------------------------------------------------------- #
intermittent = plant_data['technology'].loc[plant_data['technology']['intermittent'] == 1].index
storage = plant_data['technology'].loc[plant_data['technology']['storage'] == 1].index
dispatchable = plant_data['technology'].loc[
    (plant_data['technology']['intermittent'] == 0) & (plant_data['technology']['storage'] == 0)].index

# --------------------------------------------------------------------------- #
# %% instantiate static PARAMETERS
# --------------------------------------------------------------------------- #

# technology parameters
# TODO: one capital cost / O&M parameter for all technologies?
CAPITALCOST_G = df2gdx(db, plant_data['technology'].loc[dispatchable, 'eqacapex_p'],
                       'CAPITALCOST_G', 'par', [i_set], '[kEUR per GW]')
CAPITALCOST_R = df2gdx(db, plant_data['technology'].loc[intermittent, 'eqacapex_p'],
                       'CAPITALCOST_R', 'par', [z_set, n_set], '[kEUR per GW]')
CAPITALCOST_S = df2gdx(db, plant_data['technology'].loc[storage, 'eqacapex_p'],
                       'CAPITALCOST_S', 'par', [z_set, k_set], '[GW]')
CAPITALCOST_V = df2gdx(db, plant_data['technology'].loc[storage, 'eqacapex_e'],
                       'CAPITALCOST_V', 'par', [z_set, k_set], '[GW]')
CAPITALCOST_X = df2gdx(db, static_data['CAPCOST_X'], 'CAPITALCOST_X', 'par', [z_set], 'kEUR per GW')

EFFICIENCY_G = df2gdx(db, plant_data['technology'].loc[dispatchable, 'eta_ec'],
                      'EFFICIENCY_G', 'par', [i_set, m_set, f_set], '[%]')
EFFICIENCY_S_OUT = df2gdx(db, plant_data['technology'].loc[storage, 'eta_ec'],
                          'EFFICIENCY_S_OUT', 'par', [z_set, k_set], '[GW]')
# TODO: adjust to new inputs
EFFICIENCY_S_IN = df2gdx(db, plant_data['storage_clusters']['efficiency_in'].reorder_levels((1, 0)),
                         'EFFICIENCY_S_IN', 'par', [z_set, k_set], '[GW]')

OM_COST_G_QFIX = df2gdx(db, plant_data['technology'].loc[dispatchable, 'opex_f'],
                        'OM_COST_G_QFIX', 'par', [i_set], '[kEUR per GW]')
OM_COST_G_VAR = df2gdx(db, plant_data['technology'].loc[dispatchable, 'opex_v'],
                       'OM_COST_G_VAR', 'par', [i_set], '[kEUR per GWh]')
OM_COST_R_QFIX = df2gdx(db, plant_data['technology'].loc[intermittent, 'opex_f'],
                        'OM_COST_R_QFIX', 'par', [z_set, n_set], '[kEUR per GW]')
OM_COST_R_VAR = df2gdx(db, plant_data['technology'].loc[intermittent, 'opex_v'],
                       'OM_COST_R_VAR', 'par', [z_set, n_set], '[kEUR per GWh]')

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
INITIAL_CAP_X = df2gdx(db, dict_instantiate['CAP_X'].stack(), 'INITIAL_CAP_X', 'par', [z_set, z_set], '[GW]')

# further parameters
CO2_INTENSITY = df2gdx(db, dict_instantiate['CO2_INTENSITY'],
                       'CO2_INTENSITY', 'par', [f_set], '[kt CO2 per GWh fuel input]')
DISTANCE = df2gdx(db, dict_instantiate['DISTANCE'].stack(), 'DISTANCE', 'par', [z_set, z_set], '[km]')
# TODO: Estimate LAMBDA, i.e. the share of must-run capacity in conventional capacity
#  (controlling for renewables capacity)
LAMBDA = df2gdx(db, static_data['LAMBDA'], 'LAMBDA', 'par', 0, '[]')
PEAK_LOAD = df2gdx(db, dict_instantiate['PEAK_LOAD'], 'PEAK_LOAD', 'par', [z_set], '[GW]')
PEAK_PROFILE = df2gdx(db, dict_instantiate['PEAK_PROFILE'], 'PEAK_PROFILE', 'par', [z_set, n_set], '[]')
SIGMA = df2gdx(db, static_data['SIGMA'], 'SIGMA', 'par', 0, '[]')

VALUE_NSE = df2gdx(db, static_data['VALUE_NSE'], 'VALUE_NSE', 'par', [z_set], 'EUR per MWh')

AIR_POL_COST_FIX = df2gdx(db, static_data['AIR_POLLUTION']['fixed cost'],
                          'AIR_POL_COST_FIX', 'par', [f_set], 'EUR per MW')
AIR_POL_COST_VAR = df2gdx(db, static_data['AIR_POLLUTION']['variable cost'],
                          'AIR_POL_COST_VAR', 'par', [f_set], 'EUR per MWh')

# time series
DEMAND = df2gdx(db, ts_data['zonal'].loc[:, idx[:, :, 'load']].stack((0, 1)).reorder_levels((1, 0, 2)).round(4),
                'DEMAND', 'par', [z_set, t_set, m_set])
GEN_PROFILE = df2gdx(db, ts_data['zonal'].loc[:, idx[:, :, 'profile']].stack((0, 1)).reorder_levels((1, 0, 2)).round(4),
                     'GEN_PROFILE', 'par', [z_set, t_set, n_set])
INFLOWS = df2gdx(db, ts_data['inflows'].stack((0, 1)).reorder_levels((1, 0, 2)).astype('float').round(4),
                 'INFLOWS', 'par', [z_set, t_set, k_set])

PRICE_CO2 = df2gdx(db, ts_data['price'].loc[:, idx['EUA', :]].stack().reorder_levels((1, 0)),
                   'PRICE_CO2', 'par', [z_set, t_set])
PRICE_FUEL = df2gdx(db, ts_data['price'].drop(['EUA', 'price_day_ahead'], axis=1).stack((0, 1)).reorder_levels(
    (2, 0, 1)).round(4), 'PRICE_FUEL', 'par', [z_set, t_set, f_set])
# PRICE_DA is NOT required by model
PRICE_DA = df2gdx(db, ts_data['price'].loc[:, idx['price_day_ahead', :]].stack(), 'PRICE_DA', 'par', [t_set, z_set])

# ancillary parameters
YEAR = df2gdx(db, pd.DataFrame([cfg.year]), 'YEAR', 'par', 0, '[#]')

SWITCH_INVEST_THERM = df2gdx(db, invest_limits['thermal'], 'SWITCH_INVEST_THERM', 'par', 0, 'in {0, inf}')
SWITCH_INVEST_ITM = df2gdx(db, invest_limits['intermittent'].stack(), 'SWITCH_INVEST_ITM', 'par',
                           [z_set, n_set], 'upper invest limit')
SWITCH_INVEST_STORAGE = df2gdx(db, invest_limits['storage'].stack(), 'SWITCH_INVEST_STORAGE', 'par',
                               [z_set, k_set], 'upper limit')
SWITCH_INVEST_ATC = df2gdx(db, invest_limits['atc'].stack(), 'SWITCH_INVEST_ATC', 'par',
                           [z_set, z_set], 'upper invest limit')

logging.info('medea data exported')

# --------------------------------------------------------------------------- #
# %% data export to gdx
# --------------------------------------------------------------------------- #
export_location = os.path.join(cfg.MEDEA_ROOT_DIR, 'data', 'gdx', 'medea_main_data.gdx')
db.export(export_location)
logging.info(f'medea gdx exported to {export_location}')
