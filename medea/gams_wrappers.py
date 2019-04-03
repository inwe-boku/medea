import pandas as pd


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
    for row in df.itertuples():
        gams_parameter.add_record(row[0]).value = row[1]


def gdx2df(db_gams, symbol, symbol_type, index_list, column_list):
    """
    writes data from a GAMS gdx to a pandas dataframe.
    :param db_gams: a GAMS database object
    :param symbol: string of the GAMS symbol name
    :param symbol_type: string of symbol type ('var', 'par', 'equ')
    :param index_list:
    :param column_list:
    :return:
    """
    if symbol_type == 'var':
        gdx_dict = {tuple(obj.keys): obj.level for obj in db_gams.get_symbol(symbol)}
    elif symbol_type == 'par':
        gdx_dict = {tuple(obj.keys): obj.value for obj in db_gams.get_symbol(symbol)}
    elif symbol_type == 'equ':
        gdx_dict = {tuple(obj.keys): obj.marginal for obj in db_gams.get_symbol(symbol)}
    else:
        raise ValueError('Wrong type specified')

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
    if symbol_type is 'par':
        obj = db_gams.add_parameter_dc(symbol_name, dimension_list, desc)
        for row in df.itertuples():
            obj.add_record(row[0]).value = row[1]
    elif symbol_type is 'set':
        obj = db_gams.add_set(symbol_name, 1, desc)
        for row in df.itertuples():
            obj.add_record(row[0])
    return obj
