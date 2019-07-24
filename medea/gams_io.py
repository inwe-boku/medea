import matplotlib.pyplot as plt
import pandas as pd
from gams import *


def reset_parameter(gams_db, parameter_name, df):
    """
    writes values in df to the already existing parameter "parameter name" in GAMS-database gams_db
    :param gams_db: a GAMS database object
    :param parameter_name: a string with the parameter name
    :param df: a pandas dataframe with one line per value and all correspondong dimensions in the index
    :return: modifies gams database, does not return anything
    """
    gams_parameter = gams_db.get_parameter(parameter_name)
    gams_parameter.clear()
    if gams_parameter.get_dimension() > 0:
        for row in df.itertuples():
            gams_parameter.add_record(row[0]).value = row[1]
    elif gams_parameter.get_dimension() == 0:
        for row in df.itertuples():
            gams_parameter.add_record().value = row[1]
    else:
        raise ValueError('dimension_list must be list or integer')


def gdx2df(db_gams, symbol, index_list, column_list):
    """
    writes data from a GAMS gdx to a pandas dataframe.
    :param db_gams: a GAMS database object
    :param symbol: string of the GAMS symbol name
    :param index_list:
    :param column_list:
    :return:
    """
    sym = db_gams.get_symbol(symbol)
    if isinstance(sym, GamsParameter):
        gdx_dict = {tuple(obj.keys): obj.value for obj in sym}
    elif isinstance(sym, GamsVariable):
        gdx_dict = {tuple(obj.keys): obj.level for obj in sym}
    elif isinstance(sym, GamsEquation):
        gdx_dict = {tuple(obj.keys): obj.marginal for obj in sym}
    elif isinstance(sym, GamsSet):
        raise ValueError('gdx2df for sets not yet implemented')

    if not gdx_dict:
        gdx_df = pd.DataFrame([False], index=[symbol], columns=['Value'])
    else:
        gdx_df = pd.DataFrame(list(gdx_dict.values()), index=pd.MultiIndex.from_tuples(gdx_dict.keys()), columns=['Value'])
        gdx_df.index.names = db_gams.get_symbol(symbol).domains_as_strings
        gdx_df = pd.pivot_table(gdx_df, values='Value', index=index_list, columns=column_list)
    if 't' in index_list:
        gdx_df.reset_index(inplace=True)
        gdx_df['tix'] = pd.to_numeric(gdx_df['t'].str.split(pat='t').str.get(1))
        gdx_df.sort_values(by=['tix'], inplace=True)
        gdx_df.set_index(index_list, drop=True, inplace=True)
        gdx_df.drop(columns=['tix'], inplace=True)
    gdx_df = gdx_df.fillna(0)
    return gdx_df


def df2gdx(db_gams, df, symbol_name, symbol_type, dimension_list, desc='None'):
    """
    writes data from a pandas dataframe to a GAMS database
    :param db_gams: a GAMS database object
    :param df: a pandas dataframe with dimension as indices and one column with values
    :param symbol_name: name of the GAMS symbol as created in the GAMS database
    :param symbol_type: 'par' is parameter, 'set' is set
    :param dimension_list: list of all symbol dimensions / sets over which symbol is defined
    :param desc: optional description string
    :return: a GAMS database object
    """
    if not isinstance(df, pd.DataFrame):
        df = df.to_frame()
    if symbol_type is 'par':
        if isinstance(dimension_list, list):
            obj = db_gams.add_parameter_dc(symbol_name, dimension_list, desc)
            for row in df.itertuples():
                obj.add_record(row[0]).value = row[1]
        elif isinstance(dimension_list, int):
            obj = db_gams.add_parameter(symbol_name, dimension_list, desc)
            for row in df.itertuples():
                obj.add_record().value = row[1]
        else:
            raise ValueError('dimension_list must be list or integer')

    elif symbol_type is 'set':
        obj = db_gams.add_set(symbol_name, 1, desc)
        for row in df.itertuples():
            obj.add_record(row[0])
    else:
        raise ValueError('improper symbol_type provided')
    return obj


def gdx2plot(db_gams, symbol, index_list, column_list, base_year, slicer=None, stacked=False):
    """
    function to create plots from gdx files
    :param db_gams: a python-GAMS database
    :param symbol: name-string of symbol in GAMS database
    :param index_list: set(s) to be used as index
    :param column_list: set(s) to be used as columns
    :param base_year: year of model simulation
    :param slicer: slices the column-data
    :return:
    """
    idx = pd.IndexSlice
    df = gdx2df(db_gams, symbol, index_list, column_list)
    df = df.loc[:, (df != 0).any(axis=0)]
    if slicer:
        df = df.loc[:, idx[slicer]]

    # convert model time to actual time
    if 't' in index_list:
        start_time = pd.Timestamp(f'{base_year}-01-01')
        time_offset = pd.to_timedelta(df.index.str.replace('t', '').astype('float'), unit='h')
        model_time = start_time + time_offset
        df.index = model_time

    # plot data

    fig, ax = plt.subplots(figsize=(16, 10))  # figsize=(16, 10)

    if not stacked:
        ax.plot(df)
    elif stacked:
        ax.stackplot(df.index, df.T)

    ax.grid(b=True, which='both')

    ax.legend(df.columns.values)
    fig.autofmt_xdate()
    fig.suptitle(symbol, y=0.9975)
    fig.tight_layout()
    plt.show()
    return df
