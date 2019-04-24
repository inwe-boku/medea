import os
import subprocess
import pandas as pd
from gams import *
import config as cfg
from medea.gams_wrappers import gdx2df

"""
solves medea regional models (iteratively), compiles and writes output to csv-files 
"""


def solve(output_folder, output_name, scenario_iteration, gen_target):
    # --------------------------------------------------------------------------- #
    # initialize GAMS workspace
    # --------------------------------------------------------------------------- #
    ws = GamsWorkspace(system_directory=cfg.gams_sysdir)

    # read input data from MEDEA_data.gdx
    db_input = ws.add_database_from_gdx(
        os.path.join(cfg.folder, f'medea', 'opt', 'medea_data.gdx'))
    # read sets for clusters, hydro storage plants and products from db_input
    clust_dict = {rec.keys[0] for rec in db_input['tec']}
    hsp_dict = {rec.keys[0] for rec in db_input['tec_hsp']}
    prd_dict = {rec.keys[0] for rec in db_input['prd']}
    reg_dict = {rec.keys[0] for rec in db_input['r']}

    # TODO: Activate energy stored in reservoirs - STORAGE_LEVEL
    """
    # read stored energy from db_input
    q_enstor_dict = {tuple(rec.keys): rec.value for rec in db_input['STORAGE_LEVEL']}
    df_enstor = pd.DataFrame(list(q_enstor_dict.values()), index=pd.MultiIndex.from_tuples(q_enstor_dict.keys()))
    del q_enstor_dict
    """
    # read storage props from db_input
    df_storprop = gdx2df(db_input, 'HSP_PROPERTIES', ['tec_hsp'], ['r', 'props'])

    # read mapping of fuels to plants from EFFICIENCY parameter
    df_eff = gdx2df(db_input, 'EFFICIENCY', ['tec', 'f'], ['prd'])

    # read emission factors
    df_emf = gdx2df(db_input, 'EMISSION_INTENSITY', ['f'], [])

    # read day-ahead electricity price
    df_pda = gdx2df(db_input, 'PRICE_DA', ['t'], [])
    df_pda.columns = ['price_da']

    # --------------------------------------------------------------------------- #
    # initialize db and sets for iterations, declare parameters
    # --------------------------------------------------------------------------- #
    db_init = ws.add_database()

    # set declaration
    iter_t = db_init.add_set('t', 1, 'time periods')
    iter_start = db_init.add_set_dc('start_t', [iter_t], 'time iteration begins')
    iter_end = db_init.add_set_dc('end_t', [iter_t], 'time iteration ends')
    iter_c = db_init.add_set('tec', 1, 'power plant clusters')
    iter_c_hsp = db_init.add_set('tec_hsp', 1, 'hydro storage plants')
    iter_prd = db_init.add_set('prd', 1, 'products')
    iter_reg = db_init.add_set('r', 1, 'regions')

    # instantiate static sets
    for cluster in clust_dict:
        iter_c.add_record(cluster)
    for hsp in hsp_dict:
        iter_c_hsp.add_record(hsp)
    for ps in prd_dict:
        iter_prd.add_record(ps)
    for reg in reg_dict:
        iter_reg.add_record(reg)

    # declare parameters for iteration data
    init_gen = db_init.add_parameter_dc('INIT_GEN', [iter_reg, iter_t, iter_c, iter_prd],
                                        'initial generation at starting time')
    init_on = db_init.add_parameter_dc('INIT_ON', [iter_reg, iter_t, iter_c],
                                       'initial unit commit')
    init_turb = db_init.add_parameter_dc('INIT_TURB', [iter_reg, iter_t, iter_c_hsp],
                                         'initial generation of hydro storage plants')
    init_storage = db_init.add_parameter_dc('INIT_STORAGE', [iter_reg, iter_t, iter_c_hsp],
                                            'initial hydro storage level')
    final_storage = db_init.add_parameter_dc('FINAL_STORAGE', [iter_reg, iter_t, iter_c_hsp],
                                             'ending hydro storage level')
    init_pump = db_init.add_parameter_dc('INIT_PUMP', [iter_reg, iter_t, iter_c_hsp],
                                         'initial pumping level')

    # --------------------------------------------------------------------------- #
    # declare solution data containers (valid for all iterations)
    # --------------------------------------------------------------------------- #
    marginal_power_list = []

    # --------------------------------------------------------------------------- #
    # generate iterations
    # --------------------------------------------------------------------------- #
    os.chdir(os.path.join(cfg.folder, 'medea', 'opt'))
    for iteration in range(1, cfg.iter_num + 1):
        print(f'Iteration {iteration} in progress')

        # initialize iterations
        iter_start_time = pd.datetime(cfg.year, 1, 1, 0, 0, 0) + pd.Timedelta(
            cfg.iter_range * (iteration - 1), unit='h')
        iter_end_time = min(pd.datetime(cfg.year, 12, 31, 23, 0, 0),
                            iter_start_time + pd.Timedelta(cfg.iter_range * iteration + cfg.iter_offset,
                                                           unit='h'))
        iter_time_range = pd.date_range(iter_start_time, iter_end_time, freq='H')
        iter_start_string = f't{cfg.iter_range * (iteration - 1) + 1}'
        iter_end_string = f't{cfg.iter_range * iteration}'
        # generate time set elements for iteration
        # iter_elements = pd.DataFrame(index=iter_time_range, columns=['iter_times'])
        iter_t.clear()
        t_string = []
        for hr, val in enumerate(iter_time_range):
            iter_t.add_record(f't{hr + cfg.iter_range * (iteration - 1) + 1}')
            t_string.append(f't{hr + cfg.iter_range * (iteration - 1) + 1}')
        # add iteration start time
        iter_start.clear()
        iter_start.add_record(iter_start_string)
        # add iteration end time
        iter_end.clear()
        iter_end.add_record(iter_end_string)
        # add reservoir levels at start and end time
        init_storage.clear()
        final_storage.clear()
        # TODO: reactivate storage settings
        """
        for hsp in hsp_dict:
            init_storage.add_record((iter_start_string, hsp)).value = float(
                df_storprop.loc[hsp, 'res_size'] * df_enstor.loc[iter_start_string, 0])
            final_storage.add_record((iter_end_string, hsp)).value = float(
                df_storprop.loc[hsp, 'res_size'] * df_enstor.loc[iter_end_string, 0])
        """
        # data export for first iteration
        # if iteration == 1:
        db_init.export(os.path.join(cfg.folder, 'medea', 'opt', f'medea_{output_folder}_{output_name}_iterdata.gdx'))

        # --------------------------------------------------------------------------- #
        # call GAMS
        # --------------------------------------------------------------------------- #
        gms_in = os.path.join(cfg.folder, 'medea', 'opt', f'medea_{cfg.model_type}.gms')
        gdx_out = f'gdx=medea_{output_name}_{scenario_iteration}_{iteration}.gdx'
        subprocess.run(f'{cfg.gams_sysdir}\\gams {gms_in} {gdx_out} lo=3 --scenario={output_folder}_{output_name}')

        # ----------------------------------------------------------------------- #
        # read model solution
        # ----------------------------------------------------------------------- #
        db_solution = ws.add_database_from_gdx(
            os.path.join(cfg.folder, 'medea', 'opt', f'medea_{output_name}_{scenario_iteration}_{iteration}.gdx'))

        # check model and solve stats
        model_stat = db_solution['modelStat'].first_record().value
        solve_stat = db_solution['solveStat'].first_record().value
        if (solve_stat != 1) | ((cfg.model_type == 'linear') & (model_stat != 1)) | (
                (cfg.model_type == 'clustered') & (model_stat != 8)):
            raise StopIteration(f'Model error. Solve Stat: {"%.0f"%solve_stat}, Model Stat: {"%.0f"%model_stat}')

        # get total system cost
        obj_cost = pd.DataFrame([db_solution['cost'].first_record().level])

        read_variables = {'q_gen': (['t'], ['r', 'tec', 'prd']), 'q_fueluse': (['t'], ['r', 'tec', 'f']),
                          'res_level': (['t'], ['r', 'tec_hsp']), 'q_pump': (['t'], ['r', 'tec_hsp']),
                          'q_turbine': (['t'], ['r', 'tec_hsp']), 'q_curtail': (['t'], ['r', 'prd']),
                          'q_nonserved': (['t'], ['r', 'prd']), 'flow': (['t'], ['r', 'rr']),
                          'decommission': (['tec'], ['r']), 'invest_res': (['tec_itm'], ['r']),
                          'invest_thermal': (['tec'], ['r'])}

        result_dict = {key: gdx2df(db_solution, key, value[0], value[1])
                       for key, value in read_variables.items()}
        # TODO: what happens to dict when there are multiple solve iterations?

        # power price (marginals on balance_power equation)
        m_balpow_dict = {tuple(rec.keys): rec.marginal for rec in db_solution['SD_balance_el']}
        df_balpow = pd.DataFrame(list(m_balpow_dict.values()),
                                 index=pd.MultiIndex.from_tuples(m_balpow_dict.keys()))
        df_balpow = df_balpow.unstack(level=0)
        df_balpow.columns = df_balpow.columns.droplevel(0)
        df_balpow.reset_index(inplace=True)
        df_balpow['tix'] = pd.to_numeric(df_balpow['index'].str.split(pat='t').str.get(1))
        df_balpow.sort_values(by=['tix'], inplace=True)
        df_balpow.set_index(df_balpow['index'], drop=True, inplace=True)
        df_balpow.drop(columns=['index', 'tix'], inplace=True)

        marginal_power_list.append(df_balpow)
        marginal_power = pd.concat(marginal_power_list)

        # TODO: reactive setting of starting values
        """
        # ----------------------------------------------------------------------- #
        # set starting values for iteration
        # ----------------------------------------------------------------------- #
        if iteration < cfg.iter_num:
            init_gen.clear()
            init_turb.clear()
            init_storage.clear()
            init_pump.clear()
            next_iter_start = f't{cfg.iter_range * iteration + 1}'

            for tup in q_generation.loc[next_iter_start].itertuples():
                init_gen.add_record((next_iter_start, tup[0], 'Heat')).value = tup[1]
                init_gen.add_record((next_iter_start, tup[0], 'Power')).value = tup[2]
            for idx in q_turb.loc[next_iter_start].index:
                init_turb.add_record((next_iter_start, idx)).value = q_turb.loc[next_iter_start, idx]
            for idx in q_storagelevel.loc[next_iter_start].index:
                init_storage.add_record((next_iter_start, idx)).value = q_storagelevel.loc[next_iter_start, idx]
            for idx in q_pump.loc[next_iter_start].index:
                init_pump.add_record((next_iter_start, idx)).value = q_pump.loc[next_iter_start, idx]

            if cfg.model_type == 'clustered':
                init_on.clear()
                for idx in n_on.loc[next_iter_start].index:
                    init_on.add_record((next_iter_start, idx)).value = n_on.loc[next_iter_start, idx]

            db_init.export(os.path.join(cfg.folder, 'medea', 'opt', f'MEDEA_{output_folder}_{output_name}_iterdata.gdx'))

        if (iteration == cfg.iter_num) & (cfg.model_type == 'clustered'):
            gen_min_dict = {tuple(rec.keys): rec.value for rec in db_solution['GEN_MIN']}
            q_gen_min = pd.DataFrame(list(gen_min_dict.values()),
                                     index=pd.MultiIndex.from_tuples(gen_min_dict.keys()))
            q_gen_min = q_gen_min.unstack(level=-1)
            q_gen_min.columns = q_gen_min.columns.droplevel(0)
        """

        # --------------------------------------------------------------------------- #
        # derived solution data
        # --------------------------------------------------------------------------- #
        cols = ['Nuclear', 'Biomass', 'Lignite', 'Coal', 'Gas', 'Oil']
        df_fuelmap = df_eff.reset_index()
        df_fuelmap.set_index('tec', inplace=True)
        pgbf_list = []
        hgbf_list = []
        fubf_list = []
        emission_list = []
        for reg in cfg.regions:
            # power generation by fuel
            df_pgbf = result_dict['q_gen'].xs('Power', level=2, axis=1).xs(reg, level=0, axis=1).groupby(by=df_fuelmap['f'], axis=1).sum()
            df_pgbf.columns = pd.MultiIndex.from_product([[reg], df_pgbf.columns])
            pgbf_list.append(df_pgbf)

            # heat generation by fuel
            df_hgbf = result_dict['q_gen'].xs('Heat', level=2, axis=1).xs(reg, level=0, axis=1).groupby(by=df_fuelmap['f'], axis=1).sum()
            df_hgbf.columns = pd.MultiIndex.from_product([[reg], df_hgbf.columns])
            hgbf_list.append(df_hgbf)

            # fuel use by fuel
            df_fubf = result_dict['q_fueluse'].xs(reg, level=0, axis=1).groupby(level='f', axis=1).sum()
            df_fubf.columns = pd.MultiIndex.from_product([[reg], df_fubf.columns])
            fubf_list.append(df_fubf)

        gen_by_fuel = pd.concat(pgbf_list, axis=1).reindex(cols, level=1, axis=1)
        htgen_by_fuel = pd.concat(hgbf_list, axis=1).reindex(cols, level=1, axis=1)
        burn_by_fuel = pd.concat(fubf_list, axis=1).reindex(cols, level=1, axis=1)

        for reg in cfg.regions:
            df_emis = df_emf['Value'] * burn_by_fuel.xs(reg, axis=1)
            df_emis.columns = pd.MultiIndex.from_product([[reg], df_emis.columns])
            emission_list.append(df_emis)
        co2_emissions = pd.concat(emission_list, axis=1).reindex(cols, level=1, axis=1)
        co2_total = co2_emissions.sum().sum()

        # --------------------------------------------------------------------------- #
        # save solution to csv
        # --------------------------------------------------------------------------- #

        # check if scenario-folder exists, create if it does not exist
        if not os.path.exists(os.path.join(cfg.folder, 'medea', 'output', output_folder)):
            os.makedirs(os.path.join(cfg.folder, 'medea', 'output', output_folder))

        for key in result_dict:
            result_dict[key].to_csv(os.path.join(cfg.folder, 'medea', 'output', output_folder,
                                                 f'{key}_{output_name}_{scenario_iteration}.csv'),
                                    sep=';', encoding='utf-8')

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

    # --------------------------------------------------------------------------- #
    # delete solution gdx
    # --------------------------------------------------------------------------- #
    del db_solution
    if os.path.isfile(
            os.path.join(cfg.folder, f'medea', 'opt', f'medea_{output_name}_{scenario_iteration}_{iteration}.gdx')):
        os.remove(
            os.path.join(cfg.folder, f'medea', 'opt', f'medea_{output_name}_{scenario_iteration}_{iteration}.gdx'))

    # --------------------------------------------------------------------------- #
    # model fit - correlation & rmse
    # --------------------------------------------------------------------------- #
    gof = pd.DataFrame(columns=['correl', 'rmse_p', 'co2', 'rmse_g'])
    price_measure = pd.merge(marginal_power, df_pda, left_index=True, right_index=True)
    price_measure['sq_err'] = (price_measure['price_da'] - price_measure[0]) ** 2
    rmse = price_measure['sq_err'].mean() ** 0.5
    gen_fuel_annual = gen_by_fuel.sum()
    rmse_gen = ((gen_target - gen_fuel_annual / 1000) ** 2).mean(axis=1) ** 0.5
    correl = price_measure.corr()
    gof.loc[scenario_iteration, 'correl'] = correl.iloc[0, 1]
    gof.loc[scenario_iteration, 'rmse_p'] = rmse
    gof.loc[scenario_iteration, 'co2'] = co2_total
    gof.loc[scenario_iteration, 'rmse_g'] = rmse_gen.values
    print(f'\n Corr_p: {"%.3f" % correl.iloc[0,1]} , RMSE_p: {"%.3f" % rmse}, CO2: {"%.2f" % co2_total}, RMSE_g: {"%.2f" % rmse_gen.values} \n')
    return {'rmse_price': rmse, 'corr': correl.iloc[0, 1], 'co2': co2_total, 'rmse_gen': rmse_gen.values}
