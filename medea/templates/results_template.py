import os

import numpy as np
import pandas as pd
from gams import *

import config as cfg
from medea.gams_io import gdx2df
from medea.templates.settings_template import *

# -------------------------------------------------------------------------------------------------------------------- #
# prepare GAMS workspace
# -------------------------------------------------------------------------------------------------------------------- #
ws = GamsWorkspace(system_directory=cfg.gams_sysdir)

# specify GAMS symbols to be read from output .gdx-file along with the dimensions of the corresponding output DataFrame
# example: generate pandas DataFrame holding system cost and co2 emissions for each CO2 price scenario
symbols_to_read = {
    'cost_system': ([], ['z']),
    'emission_co2': ([], ['z'])
}

# iterate over all output .gdx-files
df_results = pd.DataFrame()
for price_co2 in range_co2price:
    # generate name of .gdx-file to read
    filename = f'medea_out_{output_naming}.gdx'.format(price_co2)
    # create database of .gdx-data
    db_output = ws.add_database_from_gdx(os.path.join(cfg.folder, 'applications', project_name, 'opt', filename))

    # read symbols from database into DataFrames with symbol name as index and CO2-price/zone as multiindex-columns
    df_i = pd.DataFrame(columns=cfg.zones)
    for symbol, sets in symbols_to_read.items():
        df = gdx2df(db_output, symbol, sets[0], sets[1])
        # set index to symbol name
        if df.index.any() == 'Value':
            df.index = [symbol]
        df_i = df_i.append(df)
        # set column names to multiindex of CO2-price and market zone
        df_i.columns = pd.MultiIndex.from_product([[f'PCO2_{price_co2}'], df_i.columns])
    df_results = pd.concat([df_results, df_i], axis=1)

# write data to disk
df_results = df_results.replace(False, np.nan)
df_results = df_results.dropna(axis=1, how='all')
df_results = df_results.sort_index(axis=1, level=1)
df_results.to_csv(os.path.join(cfg.folder, 'applications', project_name, 'results', f'out_{project_name}.csv'),
                  sep=';', encoding='utf-8', decimal=',')
