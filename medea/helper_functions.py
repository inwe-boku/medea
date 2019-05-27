import subprocess

import pandas as pd

from medea.gams_wrappers import gdx2df


def is_leapyear(year):
    """Determine whether a given year is a leapyear"""
    flag = year % 400 == 0 or (year % 4 == 0 and year % 100 != 0)
    return flag


def solve_gams(gams_dir, gms_model, gdx_out, scenario_name):
    subprocess.run(f'{gams_dir}\\gams {gms_model} {gdx_out} lo=3 --scenario={scenario_name}')


def read_solution(db_sol, model_type, read_variables):
    # check model and solve stats
    model_stat = db_sol['modelStat'].first_record().value
    solve_stat = db_sol['solveStat'].first_record().value
    if (solve_stat != 1) | ((model_type == 'linear') & (model_stat != 1)) | (
            (model_type == 'clustered') & (model_stat != 8)):
        raise StopIteration(f'Model error. Solve Stat: {"%.0f" % solve_stat}, Model Stat: {"%.0f" % model_stat}')
    # get total system cost
    obj_cost = pd.DataFrame([db_sol['cost'].first_record().level])
    # read solution variables
    result_dict = {key: gdx2df(db_sol, key, value[0], value[1])
                   for key, value in read_variables.items()}
    return obj_cost, result_dict


#df_fuelmap = df_eff.reset_index()
#df_fuelmap.set_index('tec', inplace=True)
#grouper = df_fuelmap['f']

"""
def derived_solutions(regions, result_dict, grouper):
    cols = ['Nuclear', 'Biomass', 'Lignite', 'Coal', 'Gas', 'Oil']
    pgbf_list = []
    hgbf_list = []
    fubf_list = []

    for reg in regions:
        # power generation by fuel
        df_pgbf = result_dict['q_gen'].xs('Power', level=2, axis=1).xs(reg, level=0, axis=1).groupby(
            by=grouper, axis=1).sum()
        df_pgbf.columns = pd.MultiIndex.from_product([[reg], df_pgbf.columns])
        pgbf_list.append(df_pgbf)
        # heat generation by fuel
        df_hgbf = result_dict['q_gen'].xs('Heat', level=2, axis=1).xs(reg, level=0, axis=1).groupby(
            by=grouper, axis=1).sum()
        df_hgbf.columns = pd.MultiIndex.from_product([[reg], df_hgbf.columns])
        hgbf_list.append(df_hgbf)
        # fuel use by fuel
        df_fubf = result_dict['q_fueluse'].xs(reg, level=0, axis=1).groupby(level='f', axis=1).sum()
        df_fubf.columns = pd.MultiIndex.from_product([[reg], df_fubf.columns])
        fubf_list.append(df_fubf)
    derived_dict = dict()
    derived_dict['gen_by_fuel'] = pd.concat(pgbf_list, axis=1).reindex(cols, level=1, axis=1)}
    derived_dict['htgen_by_fuel'] = pd.concat(hgbf_list, axis=1).reindex(cols, level=1, axis=1)
    derived_dict['burn_by_fuel'] = pd.concat(fubf_list, axis=1).reindex(cols, level=1, axis=1)
    return derived_dict


def dict2csv(output_folder, result_dict, scenario_name):
    # check if scenario-folder exists, create if it does not exist
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)
    for key in result_dict:
        result_dict[key].to_csv(os.path.join(output_folder, f'{key}_{scenario_name}.csv'), sep=';', encoding='utf-8')

"""


"""
# write each df to csv in scenario-specific folder
gen_by_fuel.to_csv(
    os.path.join(cfg.folder, 'medea', 'output', output_folder,
                 f'gen_power_by_fuel_{output_name}_{scenario_iteration}.csv'), sep=';', encoding='utf-8')
htgen_by_fuel.to_csv(
    os.path.join(cfg.folder, 'medea', 'output', output_folder,
                 f'gen_heat_by_fuel_{output_name}_{scenario_iteration}.csv'), sep=';', encoding='utf-8')
burn_by_fuel.to_csv(
    os.path.join(cfg.folder, 'medea', 'output', output_folder,
                 f'fuelburn_by_fuel_{output_name}_{scenario_iteration}.csv'), sep=';', encoding='utf-8')
co2_emissions.to_csv(
    os.path.join(cfg.folder, 'medea', 'output', output_folder,
                 f'emissions_{output_name}_{scenario_iteration}.csv'), sep=';', encoding='utf-8')
marginal_power.to_csv(
    os.path.join(cfg.folder, 'medea', 'output', output_folder,
                 f'price_power_{output_name}_{scenario_iteration}.csv'), sep=';', encoding='utf-8')
obj_cost.to_csv(
    os.path.join(cfg.folder, 'medea', 'output', output_folder,
                 f'total_cost_{output_name}_{scenario_iteration}.csv'), sep=';', encoding='utf-8')
"""
