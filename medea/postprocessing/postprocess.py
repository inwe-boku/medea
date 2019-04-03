# -*- coding: utf-8 -*-
"""
post-processing of results from medea_lin for emission value estimation
@author: Sebastian Wehrle
"""

import os
import pandas as pd
import numpy as np
import config as cfg


def postprocess(campaign, scenario_set, num_iter):
    for scn in scenario_set:
        # create data frames
        aggregate_generation_by_fuel = pd.DataFrame(columns=['Nuclear', 'Lignite', 'Coal', 'Gas', 'Oil', 'Biomass'])
        power_price = pd.DataFrame()
        fuel_burn = pd.DataFrame(columns=['Nuclear', 'Lignite', 'Coal', 'Gas', 'Oil', 'Biomass'])
        emission_matrix = pd.DataFrame(index=range(0, 101, 5), columns=range(0, 101, 5))
        cost_matrix = pd.DataFrame(index=range(0, 101, 5), columns=range(0, 101, 5))

        for dat in range(0, num_iter, 1):
            df_gbf = pd.read_csv(os.path.join(cfg.folder, 'medea', 'output', campaign,
                                              f'gen_power_by_fuel_{scn}_{dat}.csv'), sep=';', index_col=0)
            aggregate_generation_by_fuel = aggregate_generation_by_fuel.append(df_gbf.sum(), ignore_index=True)
            del df_gbf

            df_pr = pd.read_csv(os.path.join(cfg.folder, 'medea', 'output', campaign,
                                             f'price_power_{scn}_{dat}.csv'), sep=';', index_col=0)
            power_price[str(dat)] = df_pr['0']
            del df_pr

            df_fb = pd.read_csv(os.path.join(cfg.folder, 'medea', 'output', campaign,
                                             f'q_fuel_{scn}_{dat}.csv'), sep=';', header=[0, 1], index_col=0)
            fuel_burn_hr = df_fb.groupby(level=1, axis=1).sum()
            fuel_burn = fuel_burn.append(fuel_burn_hr.sum(), ignore_index=True)
            del df_fb

            df_co2 = pd.read_csv(os.path.join(cfg.folder, 'medea', 'output', campaign,
                                              f'emissions_{scn}_{dat}.csv'), sep=';', index_col=0)
            emission_matrix.iloc[[dat % 21], [int(np.floor(dat / 21))]] = df_co2.sum().sum() / 1000

            tot_cost = pd.read_csv(os.path.join(cfg.folder, 'medea', 'output', campaign,
                                                f'total_cost_{scn}_{dat}.csv'), sep=';', index_col=0)
            cost_matrix.iloc[[dat % 21], [int(np.floor(dat / 21))]] = float(tot_cost.values)

        # compute pass-through
        pass_through = power_price.mean().diff() / 5
        # write compiled results to excel
        writer = pd.ExcelWriter(os.path.join(cfg.folder, 'results', f'{campaign}_{scn}_compile.xlsx'),
                                engine='xlsxwriter')
        # write each df to different sheet
        power_price.to_excel(writer, sheet_name='price')
        pass_through.to_excel(writer, sheet_name='pass_through')
        aggregate_generation_by_fuel.to_excel(writer, sheet_name='annual_generation')
        fuel_burn.to_excel(writer, sheet_name='annual_fuelburn')
        emission_matrix.to_excel(writer, 'emission_matrix')
        cost_matrix.to_excel(writer, 'cost_matrix')
        # close pandas excel writer and save to excel
        writer.save()
        print(f'postprocessing of scenario {scn} complete')

# scenario_set = ['Base']
# postprocess(scenario_set)
