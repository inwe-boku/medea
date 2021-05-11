import logging
import os

import pandas as pd
from gams import *

import config as cfg
from src.utils.gams_io import df2gdx
from src.utils.preprocess_data import dict_sets, plant_data, ts_data, estimates, invest_limits

idx = pd.IndexSlice
# --------------------------------------------------------------------------- #
# %% create workspace and database
# --------------------------------------------------------------------------- #
ws = GamsWorkspace(system_directory=cfg.GMS_SYS_DIR)
db = ws.add_database()

# --------------------------------------------------------------------------- #
# %% instantiate SETS
# --------------------------------------------------------------------------- #
# energies
e_set = df2gdx(db, dict_sets['i'].append(dict_sets['f'])[~dict_sets['i'].append(dict_sets['f']).index.duplicated(
    keep='first')], 'e', 'set', 'all energy carriers')
i_set = df2gdx(db, dict_sets['i'], 'i', 'set', 'energy inputs')
f_set = df2gdx(db, dict_sets['f'], 'f', 'set', 'final energy')
# technologies
t_set = df2gdx(db, dict_sets['t'], 't', 'set', 'all technologies')
c_set = df2gdx(db, pd.DataFrame.from_dict({x: True for x in [y for y in dict_sets['t'].index if 'chp' in y]},
                                          orient='index'), 'c', 'set', [])
# c_set = df2gdx(db, dict_sets['c'], 'c', 'co-generation units')
d_set = df2gdx(db, dict_sets['d'], 'd', 'set', 'dispatchable units')
r_set = df2gdx(db, dict_sets['r'], 'r', 'set', 'intermittent units')
s_set = df2gdx(db, dict_sets['s'], 's', 'set', 'storage units')
# others
l_set = df2gdx(db, dict_sets['l'], 'l', 'set', 'limits of feasible operating regions')
h_set = df2gdx(db, dict_sets['h'], 'h', 'set', 'time steps -- hours')
z_set = df2gdx(db, dict_sets['z'], 'z', 'set', 'market zones')
#

# h_set = df2gdx(db, pd.DataFrame.from_dict({x: True for x in [y for y in dict_sets['i'].index if 'pth' in y]},
#                                           orient='index'), 'h', 'set', [])
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
AIR_POL_COST_FIX = df2gdx(db, estimates['AIR_POLLUTION']['fixed cost'],
                          'AIR_POL_COST_FIX', 'par', [e_set], 'EUR per MW')
AIR_POL_COST_VAR = df2gdx(db, estimates['AIR_POLLUTION']['variable cost'],
                          'AIR_POL_COST_VAR', 'par', [e_set], 'EUR per MWh')
# initial capacity endowment
CAPACITY = df2gdx(db, plant_data['installed'].loc[
    idx['Installed Capacity Out', :, cfg.year]].stack().droplevel(1).stack().loc[idx[:, :]],  # idx[:, dispatchable]
                  'CAPACITY', 'par', [z_set, t_set], '[GW]')
CAPACITY_X = df2gdx(db, plant_data['CAP_X'].stack().reorder_levels((0, 2, 1)),
                    'CAPACITY_X', 'par', [z_set, z_set, f_set], '[GW]')
CAPACITY_V = df2gdx(db, plant_data['installed'].loc[
    idx['Storage Capacity', :, cfg.year]].stack().stack().loc[idx[:, :, storage]],
                    'CAPACITY_STORAGE', 'par', [z_set, f_set, s_set], '[GW]')
CAPACITY_S_OUT = df2gdx(db, plant_data['installed'].loc[
    idx['Installed Capacity Out', :, cfg.year]].stack().stack().loc[idx[:, :, storage]],
                        'CAPACITY_STORE_OUT', 'par', [z_set, f_set, s_set], '[GW]')
CAPACITY_S_IN = df2gdx(db, plant_data['installed'].loc[
    idx['Installed Capacity In', :, cfg.year]].stack().stack().loc[idx[:, :, storage]],
                       'CAPACITY_STORE_IN', 'par', [z_set, f_set, s_set], '[GW]')
# # investment cost
CAPITALCOST_E = df2gdx(db, plant_data['technology'].loc[:, 'capex_e'].dropna(),
                       'CAPITALCOST_E', 'par', [s_set], '[kEUR per GW]')
CAPITALCOST_P = df2gdx(db, plant_data['technology'].loc[:, 'capex_p'],
                       'CAPITALCOST_P', 'par', [t_set], '[kEUR per GW]')
CONVERSION = df2gdx(db, plant_data['technology'].loc[:, ['eta_ec', 'primary_product', 'fuel']].set_index(
    # loc[dispatchable,
    ['primary_product', 'fuel'], append=True),
                    'CONVERSION', 'par', [t_set, f_set, e_set], '[%]')
CO2_INTENSITY = df2gdx(db, estimates['CO2_INTENSITY'],
                       'CO2_INTENSITY', 'par', [i_set], '[kt CO2 per GWh fuel input]')
COST_OM_QFIX = df2gdx(db, plant_data['technology'].loc[dispatchable, 'opex_f'],
                      'COST_OM_QFIX', 'par', [t_set], '[kEUR per GW]')
COST_OM_VAR = df2gdx(db, plant_data['technology'].loc[dispatchable, 'opex_v'],
                     'COST_OM_VAR', 'par', [t_set], '[kEUR per GWh]')
DISCOUNT_RATE = df2gdx(db, estimates['DISCOUNT_RATE'], 'DISCOUNT_RATE', 'par', [z_set], '[]')
DISTANCE = df2gdx(db, plant_data['DISTANCE'].stack(), 'DISTANCE', 'par', [z_set, z_set], '[km]')
FEASIBLE_INPUT = df2gdx(db, plant_data['chp']['fuel_need'],
                        'FEASIBLE_INPUT', 'par', [c_set, l_set, i_set], '[GW]')
FEASIBLE_OUTPUT = df2gdx(db, plant_data['chp'][['el', 'ht']].droplevel('f').stack(),
                         'FEASIBLE_OUTPUT', 'par', [c_set, l_set, f_set], '[GW]')
LAMBDA = df2gdx(db, estimates['ESTIMATES'].loc['LAMBDA', :], 'LAMBDA', 'par', [z_set], '[]')
LIFETIME = df2gdx(db, plant_data['technology'].loc[:, 'lifetime'], 'LIFETIME', 'par', [t_set], '[a]')
PEAK_LOAD = df2gdx(db, ts_data['PEAK_LOAD'], 'PEAK_LOAD', 'par', [z_set], '[GW]')
PEAK_PROFILE = df2gdx(db, ts_data['PEAK_PROFILE'], 'PEAK_PROFILE', 'par', [z_set, r_set], '[]')
# TODO: PRICE_TRADE = df2gdx(db, df, 'PRICE_TRADE', 'par', [i_set])
SIGMA = df2gdx(db, estimates['ESTIMATES'].loc['SIGMA', :], 'SIGMA', 'par', [z_set], '[]')
SWITCH_INVEST = df2gdx(db, invest_limits['thermal'], 'SWITCH_INVEST', 'par', 0, 'in {0, inf}')
VALUE_NSE = df2gdx(db, estimates['VALUE_NSE'].stack().reorder_levels((1, 0)), 'VALUE_NSE', 'par', [z_set, f_set],
                   'EUR per MWh')
# TODO: Document values of LAMBDA and SIGMA
# TODO: Add first-period energy content of storage - STORAGE_LEVEL
#
# # --------------------------------------------------------------------------- #
# # time series
# # --------------------------------------------------------------------------- #
DEMAND = df2gdx(db, ts_data['ZONAL'].loc[:, idx[:, :, 'load']].stack((0, 1)).reorder_levels((1, 0, 2)).round(4),
                'DEMAND', 'par', [z_set, h_set, f_set])
INFLOWS = df2gdx(db, ts_data['INFLOWS'].stack((0, 1)).reorder_levels((1, 0, 2)).astype('float').round(4),
                 'INFLOWS', 'par', [z_set, h_set, s_set])
PRICE = df2gdx(db, ts_data['price'].drop(['EUA', 'price_day_ahead'], axis=1).stack((0, 1)).reorder_levels(
    (2, 0, 1)).round(4), 'PRICE', 'par', [z_set, h_set, i_set])
PRICE_CO2 = df2gdx(db, ts_data['price'].loc[:, idx['EUA', :]].stack().reorder_levels((1, 0)),
                   'PRICE_CO2', 'par', [z_set, h_set])
PROFILE = df2gdx(db, ts_data['ZONAL'].loc[:, idx[:, :, 'profile']].stack((0, 1)).reorder_levels((1, 0, 2)).round(4),
                 'PROFILE', 'par', [z_set, h_set, r_set])
# PRICE_DA is NOT required by model
PRICE_DA = df2gdx(db, ts_data['price'].loc[:, idx['price_day_ahead', :]].stack(), 'PRICE_DA', 'par', [h_set, z_set])

# --------------------------------------------------------------------------- #
# ancillary parameters
# --------------------------------------------------------------------------- #
YEAR = df2gdx(db, pd.DataFrame([cfg.year]), 'YEAR', 'par', 0, '[#]')

logging.info('medea data exported')

# --------------------------------------------------------------------------- #
# %% data export to gdx
# --------------------------------------------------------------------------- #
export_location = os.path.join(cfg.MEDEA_ROOT_DIR, 'data', 'gdx', 'medea_main_data.gdx')
db.export(export_location)
logging.info(f'medea gdx exported to {export_location}')
