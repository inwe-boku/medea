import os
import numpy as np
import pandas as pd
from gams import *
import config as cfg
from medea.gams_wrappers import df2gdx
import logging

from medea.instantiation.preprocess import df_fuel, df_lim, df_prd, df_props, df_regions
from medea.instantiation.preprocess import df_tec_itm, df_tec_hsp, df_time
from medea.instantiation.preprocess import df_emission_intensity, df_itm_cap, df_itm_invest
from medea.instantiation.preprocess import data_technology, tec_props

from medea.instantiation.preprocess import fuel_set, product_set, prop_set, region_set, time_set, technology_set, \
    hydro_storage_set, intermittent_set, fuel_set_inv
from medea.instantiation.preprocess import specific_emissions, feas_op_region, itm_invest, itm_cap, \
    hyd_store_clusters, ts_medea, ntc_data

# TODO: migrate to GAMS wrappers (df2gdx)
# TODO: Add energy stored in hydro reservoirs - STORAGE_LEVEL

ws = GamsWorkspace(system_directory=cfg.gams_sysdir)
db = ws.add_database()

# --------------------------------------------------------------------------- #
# %% instantiate SETS
# --------------------------------------------------------------------------- #
f_set = df2gdx(db, df_fuel, 'f', 'set', [])
l_set = df2gdx(db, df_lim, 'l', 'set', [])
prd_set = df2gdx(db, df_prd, 'prd', 'set', [])
prop_set = df2gdx(db, df_props, 'props', 'Set', [])
r_set = df2gdx(db, df_regions, 'r', 'set', [])
tec_set = df2gdx(db, data_technology['medea_type'], 'tec', 'set', [])
tec_chp_set = df2gdx(db, pd.DataFrame.from_dict({x: True for x in [y for y in data_technology.index if 'chp' in y]},
                                                orient='index'), 'tec_chp', 'set', [])
tec_hsp_set = df2gdx(db, df_tec_hsp, 'tec_hsp', 'set', [])
tec_itm_set = df2gdx(db, df_tec_itm, 'tec_itm', 'set', [])
t_set = df2gdx(db, df_time, 't', 'set', [])



logging.info('medea sets instantiated')

"""
f_set = db.add_set('f', 1, 'fuels')
lim = db.add_set('l', 1, 'limits to feasible operating region')
prd = db.add_set('prd', 1, 'energy products')
props = db.add_set('props', 1, 'hydro storage properties')
r = db.add_set('r', 1, 'regions')
t = db.add_set('t', 1, 'time periods, hours')
tec = db.add_set('tec', 1, 'power generation technologies')
tec_chp = db.add_set('tec_chp', 1, 'cogeneration technologies')
tec_hsp = db.add_set('tec_hsp', 1, 'hydro storage technologies')
tec_itm = db.add_set('tec_itm', 1, 'intermittent technologies')
"""

# --------------------------------------------------------------------------- #
# %% instantiate static PARAMETERS
# --------------------------------------------------------------------------- #
ANCIL_SERVICE_LVL = df2gdx(db, df_ancil, 'ANCIL_SERVICE_LVL', 'par', [r_set], '[GW]')
# TODO: tec_props misses products and fuels dimensions
EFFICIENCY = df2gdx(db, tec_props.stack(-1).loc[:, 'eta'], 'EFFICIENCY', 'par', [r_set, tec_set, prd_set, f_set], '[%]')
EMISSION_INTENSITY = df2gdx(db, df_emission_intensity, 'EMISSION_INTENSITY', 'par', [f_set], '[kt CO2 per GWh fuel input]')
FEASIBLE_INPUT = df2gdx(db, df_feasible_input, 'FEASIBLE_INPUT', 'par', [tec_set, l_set, f_set], '[GW]')
FEASIBLE_OUTPUT = df2gdx(db, df_feasible_output, 'FEASIBLE_OUTPUT', 'par', [tec_set, l_set, prd_set], '[GW]')

FIXED_OM_COST = df2gdx(db, data_technology[['set_element', 'om_fix']].set_index('set_element'),
                       'FIXED_OM_COST', 'par', [tec_set], '[kEUR per GW]')
VARIABLE_OM_COST = df2gdx(db, data_technology[['set_element', 'om_var']].set_index('set_element'),
                          'VARIABLE_OM_COST', 'par', [tec_set], '[kEUR per GWh]')

HSP_PROPERTIES = df2gdx(db, 'HSP_PROPERTIES', 'par', [r_set, tec_hsp_set, prop_set])

INSTALLED_CAP_ITM = df2gdx(db, df_itm_cap, 'INSTALLED_CAP_ITM', 'par', [r_set, tec_itm_set], '[GW]')
INSTALLED_CAP_THERM = df2gdx(db, df_therm_cap, 'INSTALLED_CAP_THERM', 'par', [r_set, tec_set], '[GW]')
INVESTCOST_ITM = df2gdx(db, df_itm_invest, 'INVESTCOST_ITM', 'par', [tec_itm_set], '[kEUR per GW]')
INVESTCOST_THERMAL = df2gdx(db, data_technology[['set_element', 'annuity']].set_index('set_element'),
                            'INVESTCOST_THERMAL', 'par', [tec_set], '[kEUR per GW]')

NUM = df2gdx(db, 'NUM', 'par', [r_set, tec_set], '[#]')
TEC_SIZE = df2gdx(db, 'TEC_SIZE', 'par', [r_set, tec_set], '[]')
NTC = df2gdx(db, 'NTC', 'par', [r_set, r_set], '[GW]')
YEAR = df2gdx(db, 'YEAR', 'par', 0, '[#]')
SWITCH_INVEST_ITM = df2gdx(db, 'SWITCH_INVEST_ITM', 'par', 0, '[boolean]')
SWITCH_INVEST_THERM = df2gdx(db, 'SWITCH_INVEST_THERM', 'par', 0, '[boolean]')

logging.info('medea parameters instantiated')

# ANCIL_SERVICE_LVL = db.add_parameter_dc('ANCIL_SERVICE_LVL', [r], 'must-run for ancillary service provision')
# EFFICIENCY = db.add_parameter_dc('EFFICIENCY', [r, tec, prd, f_set], 'conversion efficiency [%]')
# EMISSION_INTENSITY = db.add_parameter_dc('EMISSION_INTENSITY', [f_set], 'specific CO2 emission of fuel burn [kt per GWh]')
# FEASIBLE_INPUT = db.add_parameter_dc('FEASIBLE_INPUT', [tec, lim, f_set], 'fuel requirement to produce output combination')
# FEASIBLE_OUTPUT = db.add_parameter_dc('FEASIBLE_OUTPUT', [tec, lim, prd], 'feasible output combinations []')
# FIXED_OM_COST = db.add_parameter_dc('OM_FIXED_COST', [tec])
# VARIABLE_OM_COST = db.add_parameter_dc('OM_VARIABLE_COST', [tec])
# HSP_PROPERTIES = db.add_parameter_dc('HSP_PROPERTIES', [r, tec_hsp, props], 'technical properties of hydro storages')
# INSTALLED_CAP_ITM = db.add_parameter_dc('INSTALLED_CAP_ITM', [r, tec_itm], 'installed capacity of intermittents [GW]')
# INSTALLED_CAP_THERM = db.add_parameter_dc('INSTALLED_CAP_THERM', [r, tec], 'installed thermal capacity [GW]')
# INVESTCOST_ITM = db.add_parameter_dc('INVESTCOST_ITM', [tec_itm], 'investment cost of intermittent technologies')
# INVESTCOST_THERMAL = db.add_parameter_dc('INVESTCOST_THERMAL', [tec], 'investment cost of thermal technologies')
# NUM = db.add_parameter_dc('NUM', [r, tec], 'number of plants per technology')
# TEC_SIZE = db.add_parameter_dc('TEC_SIZE', [r, tec], 'average capacity per technology [GW]')
# NTC = db.add_parameter_dc('NTC', [r, r], 'net transfer capacity')
# YEAR = db.add_parameter('YEAR', 0, 'data year')
# SWITCH_INVEST_THERM = db.add_parameter('SWITCH_INV_THERM', 0, 'zero or infinity')
# SWITCH_INVEST_ITM = db.add_parameter('SWITCH_INV_ITM', 0, 'zero or infinity')

# --------------------------------------------------------------------------- #
# %% instantiate dynamic PARAMETERS
# --------------------------------------------------------------------------- #
CONSUMPTION = df2gdx(db, df_consumption, 'CONSUMPTION', 'par', [r_set, t_set, prd_set])
EXPORT_FLOWS = df2gdx(db, df_exports, 'EXPORT_FLOWS', 'par', [r_set, t_set])
GEN_PROFILE = df2gdx(db, df_gen_profile, 'GEN_PROFILE', 'par', [r_set, t_set, tec_itm_set])
IMPORT_FLOWS = df2gdx(db, df_imports, 'IMPORT_FLOWS', 'par', [r_set, t_set])
NUM_AVAILABLE = df2gdx(db, df_num_avail, 'NUM_AVAILABLE', 'par', [r_set, t_set, tec_set])
PRICE_DA = df2gdx(db, df_price_da, 'PRICE_DA', 'par', [t_set])
PRICE_EUA = df2gdx(db, df_price_eua, 'PRICE_EUA', 'par', [t_set])
PRICE_FUEL = df2gdx(db, df_price_fuel, 'PRICE_FUEL', 'par', [t_set, f_set])
RESERVOIR_INFLOWS = df2gdx(db, df_res_inflows, 'RESERVOIR_INFLOWS', 'par', [r_set, t_set, tec_hsp_set])
STORAGE_LEVEL = df2gdx(db, df_storage_lvl, 'STORAGE_LEVEL', 'par', [r_set, t_set])

"""
CONSUMPTION = db.add_parameter_dc('CONSUMPTION', [r, t, prd], 'hourly consumption of power and heat [GW]')
EXPORT_FLOWS = db.add_parameter_dc('EXPORTS', [r, t], 'electricity exports to regions not modelled [MW]')
GEN_PROFILE = db.add_parameter_dc('GEN_PROFILE', [r, t, tec_itm], 'intermittent generation per GW installed')
IMPORT_FLOWS = db.add_parameter_dc('IMPORTS', [r, t], 'electricity imports from regions not modelled [MW]')
NUM_AVAILABLE = db.add_parameter_dc('NUM_AVAILABLE', [r, t, tec], 'number of plants available in cluster p in hour h')
PRICE_DA = db.add_parameter_dc('PRICE_DA', [t], 'day-ahead electricity price [thousand EUR per GWh]')
PRICE_EUA = db.add_parameter_dc('PRICE_EUA', [t], 'emission allowance price [thousand EUR per thousand t CO2]')
PRICE_FUEL = db.add_parameter_dc('PRICE_FUEL', [t, f_set], 'fuel price [thousand EUR per GWh_th]')
RESERVOIR_INFLOWS = db.add_parameter_dc('RESERVOIR_INFLOWS', [r, t, tec_hsp],
                                        'inflows to hydro storage reservoirs [GW]')
STORAGE_LEVEL = db.add_parameter_dc('STORAGE_LEVEL', [t], 'energy stored in hydro storage plants')
"""

logging.info('medea`s timeseries instantiated')

export_location = os.path.join(cfg.folder, 'medea', 'opt', 'medea_data.gdx')
db.export(export_location)
logging.info(f'medea gdx exported to {export_location}')

"""
# --------------------------------------------------------------------------- #
# %% SETS - instantiate data
# --------------------------------------------------------------------------- #
for key in fuel_set:
    f_set.add_record(key)
for limit in range(1, 6):
    lim.add_record(f'l{str(limit)}')
for elem in product_set:
    prd.add_record(elem)
for elem in prop_set:
    props.add_record(elem)
for elem in region_set:
    r.add_record(elem)
for time_stamp, time_elem in time_set.itertuples():
    t.add_record(time_elem)
for elem in technology_set.index:
    tec.add_record(elem)
    if 'chp' in elem:
        tec_chp.add_record(elem)
for elem in hydro_storage_set:
    tec_hsp.add_record(elem)
for elem in intermittent_set:
    tec_itm.add_record(elem)

logging.info('medea`s sets instantiated')

# --------------------------------------------------------------------------- #
# %% static PARAMETERS - instantiate data
# --------------------------------------------------------------------------- #

for e in specific_emissions:
    EMISSION_INTENSITY.add_record(e).value = specific_emissions[e]

for tec_type in technology_set.index:
    # invest cost and fixed om cost adjusted to 0.1 GW blocks
    FIXED_OM_COST.add_record(tec_type).value = float(technology_set.loc[tec_type, 'om_fix'] * 100)  # kEUR per 100 MW
    VARIABLE_OM_COST.add_record(tec_type).value = float(technology_set.loc[tec_type, 'om_var'])
    INVESTCOST_THERMAL.add_record(tec_type).value = float(
        (technology_set.loc[tec_type, 'annuity'] * 0.1).round(decimals=4))  # kEUR per 100 MW

    for reg in region_set:
        if technology_set.loc[tec_type, f'cap_{reg}'] > 0:
            INSTALLED_CAP_THERM.add_record((reg, tec_type)).value = float(technology_set.loc[tec_type, f'cap_{reg}'])
        # use >>f'count_{reg}'<< for actual number of plants, >>f'num_{reg}'<< for 0.1 GW blocks of plants
        if technology_set.loc[tec_type, f'num_{reg}'] > 0:
            NUM.add_record((reg, tec_type)).value = float(technology_set.loc[tec_type, f'num_{reg}'])

        output = 'power'
        if technology_set.loc[tec_type, f'eta_{reg}'] > 0:
            fl = np.floor(technology_set['medea_type'][tec_type] / 10) * 10
            EFFICIENCY.add_record((reg, tec_type, output, fuel_set_inv[fl])).value = technology_set.loc[
                tec_type, f'eta_{reg}'].round(decimals=4)

    for lm in feas_op_region['l'].drop_duplicates().tolist():
        # fuel requirements
        fl = np.floor(technology_set['medea_type'][tec_type] / 10) * 10
        FEASIBLE_INPUT.add_record((tec_type, lm, fuel_set_inv[fl])).value = \
            (float(feas_op_region.loc[(feas_op_region['set_element'] == tec_type) & (feas_op_region['l'] == lm), 'fuel_prp']) /
             technology_set.loc[tec_type, f'eta_{reg}'] / 10).round(decimals=4)
        # generation possibilities
        for output in product_set:
            FEASIBLE_OUTPUT.add_record((tec_type, lm, output)).value = \
                float(feas_op_region.loc[(feas_op_region['set_element'] == tec_type) & (
                        feas_op_region['l'] == lm), f'{output}_prp'].values) / 10

for itm_type in intermittent_set:
    INVESTCOST_ITM.add_record(itm_type).value = float(itm_invest.loc[itm_type, 'annuity'].round(decimals=4))
    for reg in region_set:
        INSTALLED_CAP_ITM.add_record((reg, itm_type)).value = itm_cap.loc[cfg.year, (reg, itm_type)]

for hsp in hydro_storage_set:
    for reg in region_set:
        for prp in prop_set:
            HSP_PROPERTIES.add_record((reg, hsp, prp)).value = float(
                hyd_store_clusters.loc[(hsp, reg), prp].round(decimals=4))

for reg in region_set:
    ANCIL_SERVICE_LVL.add_record(reg).value = (0.125 * np.nanmax(ts_medea[f'{reg}_load_power'])
                                               + 0.075 * (itm_cap.loc[cfg.year, (reg, 'wind_on')]
                                                          + itm_cap.loc[cfg.year, (reg, 'wind_off')]
                                                          + itm_cap.loc[cfg.year, (reg, 'pv')])).round(decimals=4)
    for rreg in region_set:
        if ~np.isnan(ntc_data.loc[reg, rreg]):
            NTC.add_record((reg, rreg)).value = ntc_data.loc[reg, rreg]

YEAR.add_record().value = cfg.year

if cfg.invest_conventionals:
    SWITCH_INVEST_THERM.add_record().value = float('inf')
elif ~cfg.invest_conventionals:
    SWITCH_INVEST_THERM.add_record().value = 0
else:
    logging.warning('Switch for thermal investment not set. See config file.')

if cfg.invest_renewables:
    SWITCH_INVEST_ITM.add_record().value = float('inf')
elif ~cfg.invest_renewables:
    SWITCH_INVEST_ITM.add_record().value = 0
else:
    logging.warning('Switch for intermittent investment not set. See config file.')

logging.info('medea`s static parameters instantiated')

# --------------------------------------------------------------------------- #
# %% dynamic PARAMETERS - instantiate data
# --------------------------------------------------------------------------- #

therm_fuels = ['Nuclear', 'Lignite', 'Coal', 'Gas', 'Oil', 'Biomass']

for hour in time_set.index:
    PRICE_DA.add_record(time_set.loc[hour, 'time_elements']).value = ts_medea.loc[hour, 'DE_price_day_ahead']
    PRICE_EUA.add_record(time_set.loc[hour, 'time_elements']).value = ts_medea.loc[hour, 'EUA'].round(decimals=4)

    for fuel in therm_fuels:
        PRICE_FUEL.add_record((time_set.loc[hour, 'time_elements'], fuel)).value = float(
            ts_medea.loc[hour, fuel].round(decimals=4))

    for reg in region_set:
        EXPORT_FLOWS.add_record((reg, time_set.loc[hour, 'time_elements'])).value = ts_medea.loc[hour, f'{reg}_exports']
        IMPORT_FLOWS.add_record((reg, time_set.loc[hour, 'time_elements'])).value = ts_medea.loc[hour, f'{reg}_imports']
        # STORAGE_LEVEL.add_record((time_set.loc[hour, 'time_elements'])).value = ts_medea
        for prod in product_set:
            CONSUMPTION.add_record((reg, time_set.loc[hour, 'time_elements'], prod)).value = ts_medea.loc[
                hour, f'{reg}_load_{prod}'].round(decimals=4)
        """
        for tech in technology_set:
            # NUM_AVAILABLE.add_record((reg, time_set.loc[hour, 'time_elements'], tec).value = ts_medea
        """
        for itm_tech in intermittent_set:
            if ts_medea.loc[hour, f'{reg}_{itm_tech}_profile'] > 0:
                GEN_PROFILE.add_record((reg, time_set.loc[hour, 'time_elements'], itm_tech)).value = float(
                    ts_medea.loc[hour, f'{reg}_{itm_tech}_profile'].round(decimals=4))

        for hyd in hydro_storage_set:
            if ~np.isnan(ts_medea.loc[hour, f'{reg}_inflows']):
                RESERVOIR_INFLOWS.add_record((reg, time_set.loc[hour, 'time_elements'], hyd)).value = (ts_medea.loc[
                                                                                                           hour, f'{reg}_inflows'] *
                                                                                                       hyd_store_clusters.loc[
                                                                                                           (hyd,
                                                                                                            reg), 'inflow_factor']).round(
                    decimals=4)

logging.info('medea`s timeseries instantiated')

export_location = os.path.join(cfg.folder, 'medea', 'opt', 'medea_data.gdx')
db.export(export_location)
logging.info(f'medea gdx exported to {export_location}')
"""
