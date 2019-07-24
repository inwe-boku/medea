import os
import numpy as np
import pandas as pd

from gams import *
import config as cfg
from medea.gams_io import gdx2df
# import project settings, USER MUST REPLACE {project_name} BY CORRESPONDING PROJECT NAME
from applications.{project_name}.settings_{project_name} import *


# -------------------------------------------------------------------------------------------------------------------- #
# prepare GAMS workspace
ws = GamsWorkspace(system_directory=cfg.gams_sysdir)

# specify GAMS symbols to be read from output .gdx-file along with the dimensions of the corresponding output DataFrame
symbols_to_read = {
    'cost': ([], ['r']),
    'emissions': ([], ['r'])
}

# iterate over all output .gdx-files
for price_co2 in range_co2price:
    # generate name of .gdx-file to read
    filename = f'medea_out_{output_naming}.gdx'.format(price_co2)

    # create database of .gdx-data
    db_output = ws.add_database_from_gdx(os.path.join(cfg.folder, 'applications', project_name, 'opt', filename))

    # generate dictionary holding the results for all symbols specified in symbols_to_read
    dict_results = {key: gdx2df(db_output, key, value[0], value[1]) for key, value in symbols_to_read.items()}

    # transform data as required for further analysis
    # example: generate pandas DataFrame holding system cost and co2 emissions for each CO2 price scenario
    for key, df in dict_results

    # write data to disk


    df_xxx = pd.DataFrame(columns=cfg.regions)
    for key, df in dict_results.items():
        if df.index.any() == 'Value':
            df.index = [key]
        df_xxx = df_xxx.append(df)
