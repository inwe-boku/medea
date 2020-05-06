# %% imports
import os

import pandas as pd
from gams import *

import config as cfg
from projects.asparagus.settings_asparagus import *
from src.tools.gams_io import gdx2df

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
    'add_r': (['n'], ['z']),
    'add_g': (['i'], ['z']),
    'deco_g': (['i'], ['z']),
    'AnnGByTec': (['i', 'm', 'f'], ['z'])
}
# cost_air_pol(z,f)

idx = pd.IndexSlice

# %% iterate over all output .gdx-files
df_result = pd.DataFrame(columns=cfg.zones)
for campaign in dict_campaigns.keys():
    # mix = pd.MultiIndex.from_product([dict_campaigns[campaign]['wind_cap'], cfg.zones])
    for price_co2 in dict_campaigns[campaign]['co2_price']:
        for cap_wind in dict_campaigns[campaign]['wind_cap']:
            for pv_cost in dict_campaigns[campaign]['pv_cost']:

                identifier = f'{PROJECT_NAME}_{campaign}_{price_co2}_{cap_wind}_{pv_cost}'
                FNAME = os.path.join(cfg.MEDEA_ROOT_DIR, 'projects', PROJECT_NAME, 'opt', f'medea_out_{identifier}.gdx')

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

                    # var_names.append(asdf)

                df_collect.index = pd.MultiIndex.from_product(
                    [[campaign], [price_co2], [cap_wind], [pv_cost], df_collect.index],
                    names=('campaign', 'co2_price', 'wind_cap', 'pv_cost', 'variable'))
                # add air pollution cost
                df_collect.loc[(campaign, price_co2, cap_wind, pv_cost, 'cost_airpol'), :] = air_pol_cost_by_fuel.sum()

                df_result = df_result.append(df_collect)

# %% write results to csv
df_result.index = pd.MultiIndex.from_tuples(df_result.index)
df_result.to_csv(os.path.join(cfg.MEDEA_ROOT_DIR, 'projects', PROJECT_NAME, 'results', 'results_200503.csv'),
                 sep=';', decimal=',', encoding='utf-8-sig')
