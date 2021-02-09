# %% imports
import os

import pandas as pd
from gams import *

import config as cfg
from projects.asparagus.settings_asparagus import *
from src.utils.gams_io import gdx2df

# -------------------------------------------------------------------------------------------------------------------- #
# %% prepare GAMS workspace
# -------------------------------------------------------------------------------------------------------------------- #
ws = GamsWorkspace(system_directory=cfg.GMS_SYS_DIR)

# specify GAMS symbols to be read from output .gdx-file along with the dimensions of the corresponding output DataFrame
# example: generate pandas DataFrame holding system cost and co2 emissions for each CO2 price scenario
symbols_to_read = {
    'cost_zonal': ([], ['z']),
    'AnnCO2Emissions': ([], ['z']),
    'AnnCurtail': ([], ['z']),
    'AnnG': (['m'], ['z']),
    'AnnGBiomass': ([], ['z']),
    'AnnGFossil': ([], ['z']),
    'AnnR': ([], ['z']),
    'AnnSpendingEl': ([], ['z']),
    'AnnProdSurplus': ([], ['z']),
    'AnnX': ([], ['z']),
    'AnnValueX': ([], ['z']),
    'AnnValueI': ([], ['z']),
    'AnnSIn': ([], ['z']),
    'AnnSOut': ([], ['z']),
    'AvgPriceEl': ([], ['z']),
    'AvgPriceHt': ([], ['z']),
    'cost_invest_g': ([], ['z']),
    'cost_invest_r': ([], ['z']),
    'cost_invest_sv': ([], ['z']),
    'cost_invest_x': ([], ['z']),
    'CostCO2': ([], ['z']),
    'CostFuel': ([], ['z']),
    'CostOMG': ([], ['z']),
    'CostOMR': ([], ['z']),
    'add_r': (['n'], ['z']),
    'add_g': (['i'], ['z']),
    'deco_g': (['i'], ['z']),
    'add_s': (['k'], ['z']),
    'add_v': (['k'], ['z']),
    'add_x': (['z'], ['z']),
    'cost_air_pol': (['f'], ['z']),
    'AnnGByTec': (['i', 'm', 'f'], ['z'])
}

idx = pd.IndexSlice

# %% iterate over all output .gdx-files
df_result = pd.DataFrame(columns=cfg.zones)
for campaign in dict_campaigns.keys():
    # update campaign dictionary
    dict_camp = dict_base.copy()
    dict_camp.update(dict_campaigns[campaign])

    for price_co2 in dict_camp['co2_price']:
        for cap_wind in dict_camp['wind_cap']:
            for pv_cost in dict_camp['pv_cost']:

                identifier = f'{PROJECT_NAME}_{campaign}_{price_co2}_{cap_wind}_{pv_cost}'
                FNAME = os.path.join(cfg.MEDEA_ROOT_DIR, 'projects', PROJECT_NAME, 'opt', f'medea_out_{identifier}.gdx')
                # FNAME = os.path.join('C:/Users', 'Sebastian', 'asparagus_gdx', f'medea_out_{identifier}.gdx')

                db_output = ws.add_database_from_gdx(FNAME)

                # calculation of air pollution cost
                air_pol_cost_by_fuel = gdx2df(db_output, 'cost_air_pol', ['f'], ['z'])

                df_collect = pd.DataFrame()
                for symbol, sets in symbols_to_read.items():
                    df = gdx2df(db_output, symbol, sets[0], sets[1])
                    if sets[0]:
                        strix = [f'{symbol}_{ix}' for ix in df.index]
                    else:
                        strix = [symbol]
                    df.index = strix
                    # collect results
                    df_collect = df_collect.append(df, ignore_index=False)

                df_collect.index = pd.MultiIndex.from_product(
                    [[campaign], [price_co2], [cap_wind], [pv_cost], df_collect.index],
                    names=('campaign', 'co2_price', 'wind_cap', 'pv_cost', 'variable'))
                # add air pollution cost
                df_collect.loc[(campaign, price_co2, cap_wind, pv_cost, 'cost_airpol'), :] = air_pol_cost_by_fuel.sum()

                df_result = df_result.append(df_collect)

# %% write results to csv
df_result.index = pd.MultiIndex.from_tuples(df_result.index)
df_result.to_csv(os.path.join(cfg.MEDEA_ROOT_DIR, 'projects', PROJECT_NAME, 'results', 'annual_results.csv'),
                 sep=';', decimal=',', encoding='utf-8-sig')

# %% retrieve hourly results
hourly_to_read = {
    'x': (['t', ], ['z', 'zz']),
    #    'g': (['t', ], ['z', 'i', 'm', 'f']),
    #    'r': (['t', ], ['z', 'n']),
    #    's_in': (['t', ], ['z', 'k']),
    #    's_out': (['t', ], ['z', 'k'])
}

df_hourly = pd.DataFrame()

for campaign in dict_campaigns.keys():
    # update campaign dictionary
    dict_camp = dict_base.copy()
    dict_camp.update(dict_campaigns[campaign])

    for price_co2 in dict_camp['co2_price']:
        for cap_wind in dict_camp['wind_cap']:
            for pv_cost in dict_camp['pv_cost']:

                identifier = f'{PROJECT_NAME}_{campaign}_{price_co2}_{cap_wind}_{pv_cost}'
                FNAME = os.path.join(cfg.MEDEA_ROOT_DIR, 'projects', PROJECT_NAME, 'opt', f'medea_out_{identifier}.gdx')

                db_output = ws.add_database_from_gdx(FNAME)

                df_collect = pd.DataFrame()
                for symbol, sets in hourly_to_read.items():
                    df = gdx2df(db_output, symbol, sets[0], sets[1])
                    df_collect = df_collect.append(df, ignore_index=False)

                df_collect.index = pd.MultiIndex.from_product(
                    [[campaign], [price_co2], [cap_wind], [pv_cost], df_collect.index],
                    names=('campaign', 'co2_price', 'wind_cap', 'pv_cost', 'variable'))

                df_hourly = df_hourly.append(df_collect)

# drop all zero columns
df_hourly = df_hourly.loc[:, df_hourly.any()]

# %% write hourly results to csv
df_hourly.index = pd.MultiIndex.from_tuples(df_hourly.index)
df_hourly.to_csv(os.path.join(cfg.MEDEA_ROOT_DIR, 'projects', PROJECT_NAME, 'results', 'hourly_export.csv'),
                 sep=';', decimal=',', encoding='utf-8-sig')
