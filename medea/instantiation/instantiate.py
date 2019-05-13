import logging
import os

import pandas as pd
from gams import *

import config as cfg
from medea.gams_wrappers import df2gdx
from medea.instantiation.preprocess import df_fuel, df_lim, df_prd, df_props, df_regions, df_tec_itm, df_tec_hsp, \
    df_time, data_technology, data_ntc, tec_props, df_efficiency, df_emission_intensity, df_itm_invest, df_itm_cap, \
    df_ancil, bool_invest_itm, bool_invest_thermal, df_feasops, hyd_store_clusters, ts_regional, ts_price, ts_inflows

# TODO: migrate to GAMS wrappers (df2gdx)
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
f_set = df2gdx(db, df_fuel, 'f', 'set', [])
l_set = df2gdx(db, df_lim, 'l', 'set', [])
prd_set = df2gdx(db, df_prd, 'prd', 'set', [])
prop_set = df2gdx(db, df_props, 'props', 'set', [])
r_set = df2gdx(db, df_regions, 'r', 'set', [])
tec_set = df2gdx(db, data_technology['medea_type'], 'tec', 'set', [])
tec_chp_set = df2gdx(db, pd.DataFrame.from_dict({x: True for x in [y for y in data_technology.index if 'chp' in y]},
                                                orient='index'), 'tec_chp', 'set', [])
tec_hsp_set = df2gdx(db, df_tec_hsp, 'tec_hsp', 'set', [])
tec_itm_set = df2gdx(db, df_tec_itm, 'tec_itm', 'set', [])
t_set = df2gdx(db, df_time, 't', 'set', [])

logging.info('medea sets instantiated')

# --------------------------------------------------------------------------- #
# %% instantiate static PARAMETERS
# --------------------------------------------------------------------------- #
NTC = df2gdx(db, data_ntc.stack(), 'NTC', 'par', [r_set, r_set], '[GW]')
EFFICIENCY = df2gdx(db, df_efficiency['l1'], 'EFFICIENCY', 'par', [tec_set, prd_set, f_set], '[%]')
EMISSION_INTENSITY = df2gdx(db, df_emission_intensity, 'EMISSION_INTENSITY', 'par', [f_set],
                            '[kt CO2 per GWh fuel input]')
FIXED_OM_COST = df2gdx(db, data_technology['om_fix'], 'OM_FIXED_COST', 'par', [tec_set], '[kEUR per GW]')
VARIABLE_OM_COST = df2gdx(db, data_technology['om_var'], 'OM_VARIABLE_COST', 'par', [tec_set], '[kEUR per GWh]')
INVESTCOST_ITM = df2gdx(db, df_itm_invest.stack().reorder_levels([1, 0]).round(4), 'INVESTCOST_ITM', 'par',
                        [r_set, tec_itm_set], '[kEUR per GW]')
INVESTCOST_THERMAL = df2gdx(db, data_technology['annuity'].round(4),
                            'INVESTCOST_THERMAL', 'par', [tec_set], '[kEUR per GW]')
INSTALLED_CAP_ITM = df2gdx(db, df_itm_cap, 'INSTALLED_CAP_ITM', 'par', [r_set, tec_itm_set], '[GW]')
INSTALLED_CAP_THERM = df2gdx(db, tec_props['cap'], 'INSTALLED_CAP_THERM', 'par', [r_set, tec_set], '[GW]')
NUM = df2gdx(db, tec_props['num'], 'NUM', 'par', [r_set, tec_set], '[#]')
TEC_COUNT = df2gdx(db, tec_props['count'], 'TEC_COUNT', 'par', [r_set, tec_set], '[]')
FEASIBLE_INPUT = df2gdx(db,  df_feasops['fuel_need'].round(4), 'FEASIBLE_INPUT', 'par', [tec_set, l_set, f_set], '[GW]')
FEASIBLE_OUTPUT = df2gdx(db, df_feasops[['power', 'heat']].droplevel('fuel_name').stack(), 'FEASIBLE_OUTPUT', 'par',
                         [tec_set, l_set, prd_set], '[GW]')
HSP_PROPERTIES = df2gdx(db, hyd_store_clusters[df_props.index].stack().reorder_levels([1, 0, 2]).round(4),
                        'HSP_PROPERTIES', 'par', [r_set, tec_hsp_set, prop_set])
ANCIL_SERVICE_LVL = df2gdx(db, df_ancil.round(4), 'ANCIL_SERVICE_LVL', 'par', [r_set], '[GW]')
YEAR = df2gdx(db, pd.DataFrame([cfg.year]), 'YEAR', 'par', 0, '[#]')
SWITCH_INVEST_ITM = df2gdx(db, bool_invest_itm, 'SWITCH_INVEST_ITM', 'par', 0, 'in {0, inf}')
SWITCH_INVEST_THERM = df2gdx(db, bool_invest_thermal, 'SWITCH_INVEST_THERM', 'par', 0, 'in {0, inf}')

logging.info('medea parameters instantiated')

# --------------------------------------------------------------------------- #
# %% instantiate dynamic PARAMETERS
# --------------------------------------------------------------------------- #
CONSUMPTION = df2gdx(db, ts_regional.loc[:, idx[:, :, 'load']].stack((0, 1)).reorder_levels((1, 0, 2)).round(4),
                     'CONSUMPTION', 'par', [r_set, t_set, prd_set])
EXPORT_FLOWS = df2gdx(db, ts_regional.loc[:, idx[:, 'exports', :]].stack(0).reorder_levels((1, 0)),
                      'EXPORT_FLOWS', 'par', [r_set, t_set])
IMPORT_FLOWS = df2gdx(db, ts_regional.loc[:, idx[:, 'imports', :]].stack(0).reorder_levels((1, 0)),
                      'IMPORT_FLOWS', 'par', [r_set, t_set])
GEN_PROFILE = df2gdx(db, ts_regional.loc[:, idx[:, :, 'profile']].stack((0, 1)).reorder_levels((1, 0, 2)).round(4),
                     'GEN_PROFILE', 'par', [r_set, t_set, tec_itm_set])

PRICE_DA = df2gdx(db, ts_price.loc[:, 'price_day_ahead'], 'PRICE_DA', 'par', [t_set])
PRICE_EUA = df2gdx(db, ts_price.loc[:, 'EUA'], 'PRICE_EUA', 'par', [t_set])
PRICE_FUEL = df2gdx(db, ts_price.drop(['EUA', 'price_day_ahead'], axis=1).stack().round(4),
                    'PRICE_FUEL', 'par', [t_set, f_set])
RESERVOIR_INFLOWS = df2gdx(db, ts_inflows.stack((0, 1)).reorder_levels((1, 0, 2)).round(4),
                           'RESERVOIR_INFLOWS', 'par', [r_set, t_set, tec_hsp_set])
# STORAGE_LEVEL = df2gdx(db, df_storage_lvl, 'STORAGE_LEVEL', 'par', [r_set, t_set])
# NUM_AVAILABLE = df2gdx(db, df_num_avail, 'NUM_AVAILABLE', 'par', [r_set, t_set, tec_set])

logging.info('medea`s timeseries instantiated')

# --------------------------------------------------------------------------- #
# %% data export to gdx
# --------------------------------------------------------------------------- #
export_location = os.path.join(cfg.folder, 'medea', 'opt', 'medea_data.gdx')
db.export(export_location)
logging.info(f'medea gdx exported to {export_location}')


"""
NUM_AVAILABLE = db.add_parameter_dc('NUM_AVAILABLE', [r, t, tec], 'number of plants available in cluster p in hour h')
STORAGE_LEVEL = db.add_parameter_dc('STORAGE_LEVEL', [t], 'energy stored in hydro storage plants')
# --------------------------------------------------------------------------- #
# %% dynamic PARAMETERS - instantiate data
# --------------------------------------------------------------------------- #
for hour in time_set.index:
    for reg in region_set:
        # STORAGE_LEVEL.add_record((time_set.loc[hour, 'time_elements'])).value = ts_medea
        for tech in technology_set:
            # NUM_AVAILABLE.add_record((reg, time_set.loc[hour, 'time_elements'], tec).value = ts_medea
"""
