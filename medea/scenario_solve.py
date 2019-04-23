# -*- coding: utf-8 -*-
"""
use medea_lin to estimate pass-through from emission prices to power prices
@author: Sebastian Wehrle
"""

import os
from itertools import product

import pandas as pd
from gams import *

import config as cfg
from medea.gams_wrappers import reset_parameter, gdx2df
from medea.postprocessing.postprocess import postprocess
from medea.solve import solve

# --------------------------------------------------------------------------- #
# %% definition of scaling, carbon pricing and 'setting'
# --------------------------------------------------------------------------- #
campaign = 'PsTru_ic'
# currently implemented res scalings:
# * res_pen - renewable capacity is scaled to a generation level relative to electricity demand ('penetration')
# * res_base - renewable capacity is scaled relative to res capacity in base year
scaling = 'res_base'
# currently implemented carbon price scenarios:
# * range - use a range of carbon prices from 0 to 100 EUR per t CO2 in 5 EUR per t CO2 increments
# * scaling - scale actual carbon price as in base year; default scaling factor 1
carbon_pricing = 'range'

# --------------------------------------------------------------------------- #
# %% scenario definition
# --------------------------------------------------------------------------- #
# target level for generation in 2017 [TWh]
tgt = pd.DataFrame(
    {'Nuclear': [76.3], 'Lignite': [147.5], 'Coal': [94.1], 'Gas': [89.4], 'Oil': [6.1], 'Biomass': [47.2]})

# implemented switches:
# '2030', 'PriceCoal075', 'PriceCoal125', 'CapStorage_2', 'CapStorage_10', 'CapCoal05', 'CapCoal0', 'CapLignite05',
# 'CapLignite0', 'CapGas175', 'CapGas_2', 'DemAncillary05', 'DemAncillary_0', 'DemDistHeat_0'
# all switches may be combined. For example, 'PriceCoal075_2030' projects coal prices into 2030

# scenario_set = ['Base', 'NImp075', 'NImp125', 'PriceCoal075', 'PriceCoal125', 'Base_2030', 'DemAncillary05',
#                'NImp075_2030', 'NImp125_2030', 'DemAncillary05_2030', 'PriceCoal075_2030', 'PriceCoal125_2030',
#                'CapCoal0_CapLignite0_CapGas175_2030', 'CapCoal0_CapLignite0_CapGas175_DemAncillary05_2030',
#                'CapLignite0_CapGas175_2030', 'CoalCommission_2030', 'CoalCommission_DemAncillary05_2030']

scenario_set = ['Base']

# --------------------------------------------------------------------------- #
# %% definition of 'baseline" parameters
# --------------------------------------------------------------------------- #
baseline = {
    # [plant efficiencies] -------------- #
    'e_Nuclear': [1],
    'e_Biomass': [1],
    'e_Lignite': [1.15],
    'e_Coal': [1.225],
    'e_Gas': [1.15],
    'e_Oil': [1],
    # [capacity availability of plants ] ------ #
    # 'av_Nuclear': [0.72],
    # 'av_Lignite': [0.88],
    # 'av_Coal': [0.75],
    # 'av_Coal_chp': [0.775],
    'av_Nuclear': [1.0],
    'av_Lignite': [1.0],
    'av_Coal': [1.0],
    'av_Coal_chp': [1.0],

    'av_Gas': [1.0],
    'av_Gas_chp': [1.0],
    'av_Oil': [1.0],
    'av_Biomass': [0.85],
    'av_Storage': [1],
    # [price / cost] -------------------- #
    'price_CO2': [1],
    'price_Coal': [1],
    'price_Gas': [1],
    # [exogenous generation / demand] --- #
    'c_wind_on': [1],
    'c_wind_off': [1],
    'c_pv': [1],
    'd_Heat': [1],
    'd_Power': [1],
    'd_Ancillary': [1]
}

# --------------------------------------------------------------------------- #
# %% definition of general scenario parameters
# --------------------------------------------------------------------------- #
if carbon_pricing == 'range':
    scenario_carbon = {
        'price_CO2': list(range(0, 101, 5))
    }
    baseline.update(scenario_carbon)

if scaling == 'res_pen':
    scenario_penetration = {
        'g_PV': [x/100 for x in range(0, 101, 5)],
        'g_Wind': [x/100 for x in range(0, 101, 5)]
    }
    baseline.update(scenario_penetration)

# --------------------------------------------------------------------------- #
# %% definition of specific scenario parameters
# --------------------------------------------------------------------------- #
# TODO: Use regexp to set scenario-values. Distinguish by '_', separate numbers by '-'?
# Assumptions on CURRENT renewables:
# installed wind capacities in GER 2017: 50.8 GW onshore (2000 flh), 5.4 GW offshore (4000 flh)
# installed PV capacity in GER 2017: 43 GWp
# RES expansion according to EEG 2017: PV + 2.5 GWp/a, Wind onshore + 2.9 GW/a, Wind offshore: 15 GW by 2030
# total wind energy generation in 2017: 50.8*2000 + 5.4*4000 = 123200 GWh
# projecting into 2030: 90.8 GW onshore, 15 GW offshore --> 90.8*2000 + 15*4000 = 241600 ~ 1.961 * 2017
# projecting into 2040: 119.8 GW onshore, 15 GW offshore --> 119.8*2000 + 15*4000 = 299600 ~ 2.434 * 2017

scenario_2030 = {
    # nuclear phase-out in Germany
    'av_Nuclear': [0.0],
    # assumed reduction of conventional thermal capacities by 20%
    'av_Lignite': [0.72],
    'av_Coal': [0.56],
    'av_Coal_chp': [0.72],
    'av_Gas': [0.72],
    'av_Gas_chp': [0.8],
    'av_Oil': [0.64],
    # expansion of res generation as laid out in German EEG 2017 by 2030: 90.8 GW onshore, 15 GW offshore, 73 GWp PV
    'c_wind_on': [1.808],
    'c_wind_off': [2.764],
    'c_pv': [1.724]
}
scenario_2040 = {
    # nuclear phase-out in Germany
    'av_Nuclear': [0.0],
    # assumed reduction of conventional thermal capacities by 20%
    'av_Lignite': [0.0],
    'av_Coal': [0.0],
    'av_Coal_chp': [0.0],
    'av_Gas': [2.75],
    'av_Gas_chp': [2.75],
    'av_Oil': [0.0],
    # expansion of RES as laid out in German EEG 2017 by 2040: 119.8 GW wind onshore, min 15 GW offshore, 98 GWp PV
    'c_wind_on': [2.386],
    'c_wind_off': [2.764],
    'c_pv': [2.315]
}
# double the capacity (MW, MWh) of pumped and reservoir storage, but leaves inflows unchanged!
scenario_CapStorage_2 = {
    'av_Storage': [2]
}
# tenfold increase in the capacity (MW, MWh) of pumped and reservoir storage, but leaves inflows unchanged!
scenario_CapStorage_10 = {
    'av_Storage': [10]
}
scenario_PriceCoal075 = {
    'price_Coal': [0.75]
}
scenario_PriceCoal125 = {
    'price_Coal': [1.25]
}
scenario_CapCoal05 = {
    'av_Coal': [0.35],
    'av_Coal_chp': [0.45]
}
scenario_CapCoal0 = {
    'av_Coal': [0.0],
    'av_Coal_chp': [0.0]
}
scenario_CapLignite05 = {
    'av_Lignite': [0.45]
}
scenario_CapLignite0 = {
    'av_Lignite': [0.0]
}
scenario_DemAncillary05 = {
    'd_Ancillary': [0.5]
}
scenario_DemAncillary_0 = {
    'd_Ancillary': [0.0]
}
scenario_DemDistHeat_0 = {
    'd_Heat': [0]
}
scenario_CapGas175 = {
    'av_Gas': [1.75],
    'av_Gas_chp': [1.75]
}
scenario_CapGas_2 = {
    'av_Gas': [2.0],
    'av_Gas_chp': [2.0]
}
scenario_CoalCommission = {
    'av_Lignite': [0.45],
    'av_Coal': [0.35],
    'av_Coal_chp': [0.35],
    'av_Gas': [2.0],
    'av_Gas_chp': [2.0]
}

# --------------------------------------------------------------------------- #
# %% initialize GAMS workspace and load model data
# --------------------------------------------------------------------------- #
ws = GamsWorkspace(system_directory=cfg.gams_sysdir)

db_input = ws.add_database_from_gdx(os.path.join(cfg.folder, 'medea', 'opt', 'medea_data.gdx'))
data_yr = db_input['year'].first_record().value

# read sets for clusters, hydro storage plants and products from db_input
clust_dict = {rec.keys[0] for rec in db_input['tec']}
chp_dict = {rec.keys[0] for rec in db_input['tec_chp']}
itm_dict = {rec.keys[0] for rec in db_input['tec_itm']}
hsp_dict = {rec.keys[0] for rec in db_input['props']}
prd_dict = {rec.keys[0] for rec in db_input['prd']}
fuel_dict = {rec.keys[0] for rec in db_input['f']}

# read parameters
df_eua = gdx2df(db_input, 'PRICE_EUA', ['t'], [])
df_genprofile = gdx2df(db_input, 'GEN_PROFILE', ['r', 't', 'tec_itm'], [])
df_capitm = gdx2df(db_input, 'INSTALLED_CAP_ITM', ['r', 'tec_itm'], [])
df_fuelprice = gdx2df(db_input, 'PRICE_FUEL', ['t', 'f'], [])
df_eff = gdx2df(db_input, 'EFFICIENCY', ['tec', 'prd', 'f'], [])
df_feasgen = gdx2df(db_input, 'FEASIBLE_OUTPUT', ['tec', 'l', 'prd'], [])
df_fuelreq = gdx2df(db_input, 'FEASIBLE_INPUT', ['tec', 'l', 'f'], [])
df_store_props = gdx2df(db_input, 'HSP_PROPERTIES', ['r', 'tec_hsp', 'props'], [])
df_ancillary = gdx2df(db_input, 'ANCIL_SERVICE_LVL', ['r'], [])
df_load = gdx2df(db_input, 'CONSUMPTION', ['r', 't', 'prd'], [])

# --------------------------------------------------------------------------- #
# %% scenario generation
# --------------------------------------------------------------------------- #
os.chdir(os.path.join(cfg.folder, 'medea', 'opt'))
idx = pd.IndexSlice
traded_fuels = ['Nuclear', 'Lignite', 'Gas', 'Oil', 'Coal', 'Biomass']

for scn in scenario_set:
    scenario_name = f'{campaign}_{scn}'

    # --------------------------------------------------------------------------- #
    # scenario generation
    # --------------------------------------------------------------------------- #
    scenario_compilation = baseline

    if '2030' in scn:
        scenario_compilation.update(scenario_2030)
    if '2040' in scn:
        scenario_compilation.update(scenario_2040)
    # Prices
    if 'PriceCoal075' in scn:
        scenario_compilation.update(scenario_PriceCoal075)
    if 'PriceCoal125' in scn:
        scenario_compilation.update(scenario_PriceCoal125)
    # Capacities
    if 'CapStorage_2' in scn:
        scenario_compilation.update(scenario_CapStorage_2)
    if 'CapStorage_10' in scn:
        scenario_compilation.update(scenario_CapStorage_10)
    if 'CapCoal05' in scn:
        scenario_compilation.update(scenario_CapCoal05)
    if 'CapCoal0' in scn:
        scenario_compilation.update(scenario_CapCoal0)
    if 'CapLignite05' in scn:
        scenario_compilation.update(scenario_CapLignite05)
    if 'CapLignite0' in scn:
        scenario_compilation.update(scenario_CapLignite0)
    if 'CapGas175' in scn:
        scenario_compilation.update(scenario_CapGas175)
    if 'CapGas_2' in scn:
        scenario_compilation.update(scenario_CapGas_2)
    # Demand / Consumption
    if 'DemAncillary_0' in scn:
        scenario_compilation.update(scenario_DemAncillary_0)
    if 'DemAncillary05' in scn:
        scenario_compilation.update(scenario_DemAncillary05)
    if 'DemDistHeat_0' in scn:
        scenario_compilation.update(scenario_DemDistHeat_0)
    if 'CoalCommission' in scn:
        scenario_compilation.update(scenario_CoalCommission)

    scenarios = pd.DataFrame(list(product(*scenario_compilation.values())), columns=scenario_compilation.keys())

    # --------------------------------------------------------------------------- #
    # prepare scenario iterations
    # --------------------------------------------------------------------------- #
    goodness_of_fit = pd.DataFrame(columns=['rmse', 'corr'])
    tec2fuel_map = gdx2df(db_input, 'EFFICIENCY', ['tec', 'f'], ['prd']).reset_index()
    tec2fuel_map = tec2fuel_map.loc[tec2fuel_map['tec'].isin(df_feasgen.index.get_level_values(0)), :]
    traded_fuels = ['Nuclear', 'Lignite', 'Gas', 'Oil', 'Coal']
    year_range = pd.date_range(pd.datetime(cfg.year, 1, 1, 0, 0, 0), end=pd.datetime(cfg.year, 12, 31, 23, 0, 0),
                               freq='H')
    # generate elements of time set t
    time_periods = pd.DataFrame(index=year_range, columns=['time_elements'])
    for hr, val in enumerate(year_range):
        time_periods['time_elements'].loc[year_range[hr]] = f't{hr + 1}'

    # --------------------------------------------------------------------------- #
    # iterate over scenarios and set parameters accordingly
    # --------------------------------------------------------------------------- #
    for scenario_iteration in range(0, len(scenarios)):

        # ancillary services requirement
        df_ancillary_mod = df_ancillary * scenarios.loc[scenario_iteration, 'd_Ancillary']
        reset_parameter(db_input, 'ANCIL_SERVICE_LVL', df_ancillary_mod)

        # efficiency
        df_eff_mod = df_eff
        for fl in traded_fuels:
            df_eff_mod.loc[idx[:, :, fl], :] = \
                df_eff.loc[idx[:, :, fl], :] * scenarios.loc[scenario_iteration, f'e_{fl}']
        reset_parameter(db_input, 'EFFICIENCY', df_eff)

        # feasible input of thermal plants
        df_fuelreq_mod = df_fuelreq
        for fl in traded_fuels:
            df_fuelreq_mod.loc[idx[:, :, fl], :] = \
                df_fuelreq.loc[idx[:, :, fl], :] / scenarios.loc[scenario_iteration, f'e_{fl}']
        reset_parameter(db_input, 'FEASIBLE_INPUT', df_fuelreq_mod)
        
        # feasible output of thermal plants
        df_feasgen_mod = df_feasgen
        for fl in traded_fuels:
            df_feasgen_mod.loc[tec2fuel_map.loc[tec2fuel_map['f'] == fl, 'tec'], :] = \
                df_feasgen_mod.loc[tec2fuel_map.loc[tec2fuel_map['f'] == fl, 'tec'], :] * scenarios.loc[scenario_iteration, f'av_{fl}']
        reset_parameter(db_input, 'FEASIBLE_OUTPUT', df_feasgen_mod)

        # installed capacity of intermittents
        df_capitm_mod = df_capitm

        if scaling == 'res_base':
            for itm in itm_dict:
                if itm != 'ror':
                    df_capitm_mod.loc[idx[:, itm], :] = \
                        df_capitm.loc[idx[:, itm], :] * scenarios.loc[scenario_iteration, f'c_{itm}']
        elif scaling == 'res_pen':
            for itm in itm_dict:
                if itm != 'ror':
                    df_capitm_mod.loc[idx[:, itm], 'Value'] = \
                        (df_load.loc[idx[:, :, 'Power'], :].groupby('r').sum() *
                         scenarios.loc[scenario_iteration, f'c_{itm}'] /
                         df_genprofile.loc[idx[:, :, itm], :].groupby('r').sum()).values
        reset_parameter(db_input, 'INSTALLED_CAP_ITM', df_capitm_mod)
        
        # carbon dioxide emission price
        df_eua_mod = df_eua
        if carbon_pricing == 'range':
            df_eua_mod['Value'] = scenarios.loc[scenario_iteration, 'price_CO2']
        elif carbon_pricing == 'scaling':
            df_eua_mod = df_eua_mod * scenarios.loc[scenario_iteration, 'price_CO2']
        else:
            raise ValueError('Carbon pricing parameter not set.')
        reset_parameter(db_input, 'PRICE_EUA', df_eua_mod)

        # fuel price
        df_fuelprice_mod = df_fuelprice
        for fl in traded_fuels:
            if not scenarios.filter(like=f'price_{fl}').columns.empty:
                df_fuelprice_mod.loc[idx[:, fl], :] = \
                    df_fuelprice_mod.loc[idx[:, fl], :] * scenarios.loc[scenario_iteration, f'price_{fl}']
        reset_parameter(db_input, 'PRICE_FUEL', df_fuelprice_mod)
        
        # hydro storage properties
        df_store_props_mod = df_store_props
        for prp in hsp_dict:
            if 'cap' in prp:
                df_store_props_mod.loc[idx[:, :, prp], :] = \
                    df_store_props_mod.loc[idx[:, :, prp], :] * scenarios.loc[scenario_iteration, 'av_Storage']
        reset_parameter(db_input, 'HSP_PROPERTIES', df_store_props_mod)
        
        # energy consumption
        df_load_mod = df_load
        for prd in prd_dict:
            df_load_mod.loc[idx[:, :, prd], :] = \
                df_load_mod.loc[idx[:, :, prd], :] * scenarios.loc[scenario_iteration, f'd_{prd}']
        reset_parameter(db_input, 'CONSUMPTION', df_load_mod)

        # export scenario data to database
        export_location = os.path.join(cfg.folder, 'medea', 'opt', f'MEDEA_{scenario_name}_data.gdx')
        db_input.export(export_location)

        # call iterative model solution
        goodfit = solve(campaign, scn, scenario_iteration, gen_target=tgt)
# TODO: reactivate goodsness of fit tracking, when issue in solve.py is resolved
#        for key in goodfit.keys():
#            goodness_of_fit.loc[scenario_iteration, key] = goodfit[key]

        # delete scenario data file
    if os.path.isfile(os.path.join(cfg.folder, 'medea', 'opt', f'MEDEA_{scenario_name}_data.gdx')):
        os.remove(os.path.join(cfg.folder, 'medea', 'opt', f'MEDEA_{scenario_name}_data.gdx'))

        # --------------------------------------------------------------------------- #
        # postprocessing and aggregation of results
        # --------------------------------------------------------------------------- #
    print(f'Postprocessing scenario {scn}')
    postprocess(campaign, [scn], num_iter=len(scenarios))
