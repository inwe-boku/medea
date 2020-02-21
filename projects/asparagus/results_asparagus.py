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
}
# cost_air_pol(z,f)
var_names = ['syscost', 'co2emission', 'curtail', 'gen_el', 'gen_ht', 'gen_biomass', 'gen_renew', 'cons_spend',
             'prod_surplus', 'exports', 'export_value', 'import_value', 'in_storages',
             'gen_storages', 'price_el', 'price_ht', 'add_pv', 'add_ror', 'add_wind_off', 'add_wind_on', 'add_nuc',
             'add_lig_stm', 'add_lig_stm_chp', 'add_lig_boa', 'add_lig_boa_chp', 'add_coal_sub', 'add_coal_sub_chp',
             'add_coal_sc', 'add_coal_sc_chp', 'add_ng_stm', 'add_ng_stm_chp', 'add_ng_cbt_lo', 'add_ng_cbt_lo_chp',
             'add_ng_cbt_hi', 'add_ng_cbt_hi_chp', 'add_ng_cc_lo', 'add_ng_cc_lo_chp', 'add_ng_cc_hi',
             'add_ng_cc_hi_chp', 'add_ng_mtr', 'add_ng_mtr_chp', 'add_oil_stm', 'add_oil_stm_chp', 'add_oil_cbt',
             'add_oil_cbt_chp', 'add_oil_cc', 'add_bio', 'add_bio_chp', 'add_ng_boiler_chp', 'add_heatpump_pth']

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
                    # collect results
                    df_collect = df_collect.append(df, ignore_index=True)

                df_collect.index = pd.MultiIndex.from_product(
                    [[campaign], [price_co2], [cap_wind], [pv_cost], var_names],
                    names=('campaign', 'co2_price', 'wind_cap', 'pv_cost', 'variable'))
                # add air pollution cost
                df_collect.loc[(campaign, price_co2, cap_wind, pv_cost, 'cost_airpol'), :] = air_pol_cost_by_fuel.sum()

                df_result = df_result.append(df_collect)

# %% write results to csv
df_result.index = pd.MultiIndex.from_tuples(df_result.index)
df_result.to_csv(os.path.join(cfg.MEDEA_ROOT_DIR, 'projects', PROJECT_NAME, 'results', 'results.csv'),
                 sep=';', decimal=',', encoding='utf-8-sig')
