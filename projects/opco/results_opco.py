import os

import pandas as pd
from gams import *

import config as cfg
from projects.opco.settings_opco import *
from src.utils.gams_io import gdx2df

idx = pd.IndexSlice
# -------------------------------------------------------------------------------------------------------------------- #
# %% prepare GAMS workspace
# -------------------------------------------------------------------------------------------------------------------- #
ws = GamsWorkspace(system_directory=cfg.GMS_SYS_DIR)

# specify GAMS symbols to be read from output .gdx-file along with the dimensions of the corresponding output DataFrame
# example: generate pandas DataFrame holding system cost and co2 emissions for each CO2 price scenario
symbols_to_read = {
    'cost_zonal': ([], ['z']),
    'emission_co2': ([], ['z']),
    'add_r': (['n'], ['z'])
}

# %% iterate over all output .gdx-files
df_result = pd.DataFrame(columns=cfg.zones)
for campaign in dict_campaigns.keys():
    # update campaign dictionary
    dict_camp = dict_base.copy()
    dict_camp.update(dict_campaigns[campaign])

    for re_share in dict_camp['re_share']:
        for wind_limit in dict_camp['wind_on_cap']:
            for price_co2 in dict_camp['carbon_price']:
                for budget_co2 in dict_camp['carbon_limit']:
                    identifier = f'{PROJECT_NAME}_{campaign}_{re_share}_{wind_limit}_{price_co2}_{budget_co2}'
                    FNAME = os.path.join(cfg.MEDEA_ROOT_DIR, 'projects', PROJECT_NAME, 'opt',
                                         f'medea_out_{identifier}.gdx')

                    db_output = ws.add_database_from_gdx(FNAME)

                    # calculation of air pollution cost
                    # air_pol_cost_by_fuel = gdx2df(db_output, 'cost_air_pol', ['f'], ['z'])

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
                        [[campaign], [re_share], [wind_limit], [price_co2], [budget_co2], df_collect.index],
                        names=('campaign', 're_share', 'wind_cap', 'carb_price', 'carb_limit', 'variable'))
                    # add air pollution cost
                    # df_collect.loc[(campaign, re_share, wind_limit, 'cost_airpol'), :] = air_pol_cost_by_fuel.sum()

                    df_result = df_result.append(df_collect)

# %% write results to csv
df_result.index = pd.MultiIndex.from_tuples(df_result.index)
df_result.to_csv(os.path.join(cfg.MEDEA_ROOT_DIR, 'projects', PROJECT_NAME, 'results', 'annual_results.csv'),
                 sep=';', decimal=',', encoding='utf-8-sig')
