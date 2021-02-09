import os
import subprocess

import matplotlib.pyplot as plt
import pandas as pd
from gams import *

import config as cfg


def timesort(df, index_sets='t', timeindex_name='t', timeindex_string='t'):
    """
    Sorts a pandas dataframe indexed by a string-float combination by float (ignoring string) in descending order.
    Useful for sorting GAMS-time-set-indexed data.
    :param df: A dataframe indexed by a float-string combination
    :param index_sets: column name(s) to be used as index
    :param timeindex_name: name of df's index. Defaults to 't'
    :param timeindex_string:
    :return:
    """
    df.reset_index(inplace=True)
    df['tix'] = pd.to_numeric(df[timeindex_name].str.split(pat=timeindex_string).str.get(1))
    df.sort_values(by=['tix'], inplace=True)
    df.set_index(index_sets, drop=True, inplace=True)
    df.drop(columns=['tix'], inplace=True)
    return df


def reset_symbol(db_gams, symbol_name, df):
    """
    writes values in df to the already existing symbol "symbol name" in GAMS-database gams_db
    :param db_gams: a GAMS database object
    :param symbol_name: a string with the symbol name
    :param df: a pandas dataframe with one line per value and all correspondong dimensions in the index
    :return: modifies gams database, does not return anything
    """
    gams_symbol = db_gams.get_symbol(symbol_name)
    gams_symbol.clear()
    if gams_symbol.get_dimension() > 0:
        for row in df.itertuples():
            gams_symbol.add_record(row[0]).value = row[1]
    elif gams_symbol.get_dimension() == 0:
        for row in df.itertuples():
            gams_symbol.add_record().value = row[1]
    else:
        raise ValueError('dimension_list must be list or integer')


def gdx2df(db_gams, symbol, index_list, column_list, check_sets=False):
    """
    writes data from a GAMS gdx to a pandas dataframe.
    :param db_gams: a GAMS database object
    :param symbol: string of the GAMS symbol name
    :param index_list: a list of strings of GAMS-sets over which 'symbol' is defined which constitute the df's index
    :param column_list: a list of strings of GAMS-sets over which 'symbol' is defined which constitute the df's columns
    :param check_sets:
    :return: a pd.DataFrame
    """
    sym = db_gams.get_symbol(symbol)
    if isinstance(sym, GamsParameter):
        gdx_dict = {tuple(obj.keys): obj.value for obj in sym}
    elif isinstance(sym, GamsVariable):
        gdx_dict = {tuple(obj.keys): obj.level for obj in sym}
    elif isinstance(sym, GamsEquation):
        gdx_dict = {tuple(obj.keys): obj.marginal for obj in sym}
    elif isinstance(sym, GamsSet):
        gdx_dict = {obj.keys[0] for obj in sym}
    else:
        raise ValueError('Symbol not in gdx')

    if not gdx_dict:
        gdx_df = pd.DataFrame([False], index=[symbol], columns=['Value'])
    elif isinstance(sym, GamsSet):
        gdx_df = pd.DataFrame(data=True, index=gdx_dict, columns=['Value'])
    else:
        gdx_df = pd.DataFrame(list(gdx_dict.values()), index=pd.MultiIndex.from_tuples(gdx_dict.keys()),
                              columns=['Value'])
        gdx_df.index.names = db_gams.get_symbol(symbol).domains_as_strings
        gdx_df = pd.pivot_table(gdx_df, values='Value', index=index_list, columns=column_list)
    if 't' in index_list:
        gdx_df = timesort(gdx_df, index_sets=index_list)
    # if check_sets and (isinstance(sym, GamsParameter) or isinstance(sym, GamsVariable)):
    #    gdx_index_set = {obj.keys[0] for obj in sym}

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
    :param stacked:
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


def run_medea(gms_exe_dir, gms_model, medea_project, project_scenario, export_location):
    """
    flexible run of power system model medea
    :param gms_exe_dir: string of path to GAMS executable
    :param gms_model: string of path to GAMS model to solve
    :param medea_project: string of medea-project name
    :param project_scenario: string of project-scenario (typically one iteration)
    :param export_location: string of path where to save results
    :return:
    """
    # generate identifier of scenario output
    gdx_out = f'gdx=medea_out_{project_scenario}.gdx'
    # call GAMS to solve model / scenario
    subprocess.run(
        f'{gms_exe_dir}\\gams {gms_model} {gdx_out} lo=3 o=nul --project={medea_project} --scenario={project_scenario}')
    # clean up after each run and delete input data (which is also included in output, so no information lost)
    if os.path.isfile(export_location):
        os.remove(export_location)


def run_medea_project(project_name, scenario_id):
    """
    runs / solves a project of power system model medea with strict project directory conventions
    :param project_name: string of medea-project name
    :param scenario_id: string of project-scenario (typically one iteration)
    :return:
    """
    # generate file names
    gms_model_fname = os.path.join(cfg.MEDEA_ROOT_DIR, 'projects', project_name, 'opt', 'medea_main.gms')
    gdx_out_fname = f'gdx=medea_out_{scenario_id}.gdx'
    input_fname = os.path.join(cfg.MEDEA_ROOT_DIR, 'projects', project_name, 'opt', f'medea_{scenario_id}_data.gdx')

    # call GAMS to solve model / scenario
    subprocess.run(
        f'{cfg.GMS_SYS_DIR}\\gams {gms_model_fname} {gdx_out_fname} lo=3 o=nul --project={project_name} --scenario={scenario_id}')
    # clean up after each run and delete input data (which is also included in output, so no information lost)
    if os.path.isfile(input_fname):
        os.remove(input_fname)


def run_medea_test(test_data_name):
    """
    runs / solves a project of power system model medea with strict project directory conventions
    :return:
    """
    # generate file names
    gms_model_fname = os.path.join(cfg.MEDEA_ROOT_DIR, 'tests', 'opt', 'medea_main.gms')
    gdx_out_fname = f'gdx=medea_out_{test_data_name}.gdx'
    input_fname = os.path.join(cfg.MEDEA_ROOT_DIR, 'tests', 'opt', f'medea_{test_data_name}_data.gdx')

    # call GAMS to solve model / scenario
    subprocess.run(
        f'{cfg.GMS_SYS_DIR}\\gams {gms_model_fname} {gdx_out_fname} lo=3 --project=test --scenario={test_data_name}')
    # clean up after each run and delete input data (which is also included in output, so no information lost)
    if os.path.isfile(input_fname):
        os.remove(input_fname)
