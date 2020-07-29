# %% imports
import os

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

import config as cfg
from src.tools.visualize_data import plot_lines, plot_sublines, plot_subn

# %% ----- ----- ----- ----- settings ----- ----- ----- -----
idx = pd.IndexSlice
PRICE_CO2 = 50

scenario = 'base'

REFUEL_COLORS = ['#c72321', '#0d8085', '#f0c220', '#595959', '#3b68f9', '#7794dd']
RES_COLORS = ['#d69602', '#ffd53d', '#3758ba', '#7794dd']
RES_COLORS3 = ['#d69602', '#e5b710', '#ffd53d', '#3758ba', '#3b68f9', '#7794dd']
RES_COLORS2 = ['#ffd53d', '#3758ba']

ANNUITY_FACTOR = 0.05827816
FLH_PV = 857.4938
FLH_WINDON = 2015.0359

RPATH = os.path.join(cfg.MEDEA_ROOT_DIR, 'projects', 'asparagus', 'results')
FPATH = os.path.join(cfg.MEDEA_ROOT_DIR, 'projects', 'asparagus', 'doc', 'figures')

if not os.path.exists(FPATH):
    os.makedirs(FPATH)

# %% ----- ----- ----- ----- read results ----- ----- ----- -----
# results_h2stack = pd.read_csv(os.path.join(RPATH, 'results_h2stack.csv'), decimal=',', delimiter=';', index_col=[0, 1, 2, 3, 4], header=[0])
# results_sens = pd.read_csv(os.path.join(RPATH, 'results_h2_pvsens.csv'), decimal=',', delimiter=';', index_col=[0, 1, 2, 3, 4], header=[0])
# results = results_h2stack.append(results_sens)

results = pd.read_csv(os.path.join(RPATH, 'results_h2.csv'), decimal=',', delimiter=';', index_col=[0, 1, 2, 3, 4],
                      header=[0])
results = results.unstack(-1)

# %% plot annual system cost in Austria for scenarios with co2-price > 0


# %% plot annual system cost less trade balance and financial trade balance in Austria


# %% plot annual CO2 emissions in Austria for each scenario


# %% annual plot renewable generation, curtailment and net trade volume in Austria


# %% plot seasonal (monthly) variation in ror, inflows, wind, pv resources


# %% plot filling of reservoirs v over year for each scenario in baseline


# %% analyze system configuration (capacities added and decommissioned)
cap_init_at = {
    'ng_stm': 0.13932,
    'ng_stm_chp': 0.606472,
    'ng_cbt_lo': 0.1282346,
    'ng_cbt_lo_chp': 0.27724938,
    'ng_cc_lo': 0.15136,
    'ng_cc_lo_chp': 0.32938,
    'ng_cc_hi_chp': 2.286138,
    'oil_stm': 0.08584,
    'oil_cbt': 0.003915,
    'oil_cbt_chp': 0.04756,
    'oil_cc': 0.0348,
    'bio': 0.354965,
    'bio_chp': 0.369499,
    'ng_boiler_chp': 3.87,
    'heatpump_pth': 0.1
}

capi = pd.DataFrame.from_dict(cap_init_at, orient='index', columns=['base'])
capi.columns.name = 'scenario'
capi.index.name = 'variable'

capa = results.loc[idx[scenario, PRICE_CO2, :, 36715], idx['AT', :]]
capa.columns = capa.columns.droplevel(0)
capa = capa.loc[:, (capa.columns.str.contains('add_g') | capa.columns.str.contains('deco'))]
capa.columns = pd.MultiIndex.from_tuples(list(capa.columns.str.split('_g_')))
capa.loc[:, idx['deco', :]] = - capa.loc[:, idx['deco', :]]
capa = capa.groupby(level=1, axis=1).sum()
capa.columns.name = 'variable'
capa.index = capa.index.rename(['scenario', 'co2price', 'wind_lim', 'pv_cost'])
capa = (capa + capi.T).dropna(axis=1, how='all')
capa = capa.replace(0, np.nan).dropna(axis=1, how='all').replace(np.nan, 0)
capa.index = capa.index.get_level_values(2)

plot_lines(capa, os.path.join(FPATH, 'capacity.pdf'))  #, color=REFUEL_COLORS)

# %% analyze system operation (net exports, curtailment, generation)
var_of_interest = ['AnnCO2Emissions', 'AnnCurtail', 'AnnCurtailShare', 'AnnGBiomass', 'AnnGFossil_el', 'AnnG_el',
                   'AnnR', 'AnnSIn', 'AnnSOut', 'AnnX']

oper = results.loc[idx[scenario, :, :, 36715], idx['AT', :]]
oper.loc[:, idx['AT', 'AnnX']] = results.loc[:, idx['DE', 'AnnX']]
oper.columns = oper.columns.droplevel(0)
oper['AnnGFossil_el'] = oper['AnnG_el'] - oper['AnnGBiomass']
oper['AnnCurtailShare'] = oper['AnnCurtail'] / oper['AnnR']
oper.index = oper.index.droplevel([0, 3])

for var in var_of_interest:
    plot_lines(oper.loc[:, var].unstack(0), os.path.join(FPATH, f'oper_{var}.pdf'), color=REFUEL_COLORS)

# oper = oper.loc[:, oper.columns.str.contains('AnnGByTec')]
# oper.columns = oper.columns.str.replace('AnnGByTec_', '')  #.str.replace('(', '').str.replace(')', '')
# oper.columns = pd.MultiIndex.from_tuples(list(oper.columns.str.split('_g_')))


# %% ----- ----- ----- plot wind restriction: changes in system operation ----- ----- -----
# net electricity generation, net electricity exports, fossil thermal generation, CO2 emissions from energy generation

# prepare data
restrict_sysops = results.loc[idx[scenario, PRICE_CO2, :, 36715], idx['AT', ['AnnG_el', 'AnnGBiomass', 'AnnSOut',
                                                                             'AnnSIn', 'AnnR', 'AnnCO2Emissions']]]
restrict_sysops[('AT', 'AnnX')] = results.loc[idx[scenario, PRICE_CO2, :, 36715], idx['DE', 'AnnX']]
restrict_sysops.index = restrict_sysops.index.droplevel([0, 1, 3])
restrict_sysops.columns = restrict_sysops.columns.droplevel(0)
restrict_sysops['Net electricity generation'] = (restrict_sysops[['AnnG_el', 'AnnSOut', 'AnnR']].sum(axis=1)
                                                 - restrict_sysops['AnnSIn'])
restrict_sysops['Fossil thermal generation'] = restrict_sysops['AnnG_el'] - restrict_sysops['AnnGBiomass']
restrict_sysops = restrict_sysops.drop(['AnnGBiomass', 'AnnG_el', 'AnnR', 'AnnSOut', 'AnnSIn'], axis=1)
restrict_sysops = restrict_sysops.rename(columns={'AnnCO2Emissions': rf'CO$_2$ emissions from energy generation',
                                                  'AnnX': 'Net electricity exports'})
restrict_sysops = restrict_sysops[['Net electricity generation', 'Net electricity exports',
                                   'Fossil thermal generation', rf'CO$_2$ emissions from energy generation']]

# plot data
plot_subn(restrict_sysops / 1000, os.path.join(FPATH, 'sysops.pdf'), xlim=[18, 0], color=REFUEL_COLORS,
          xlabel='Added Capacity of Wind [GW]', ylabel=['TWh', 'TWh', 'TWh', 'million t'])

plot_lines(restrict_sysops[rf'CO$_2$ emissions from energy generation'] / 1000, os.path.join(FPATH, 'co2emissions.pdf'),
           xlim=[18, 0], color=REFUEL_COLORS, xlabel='Added Capacity of Wind [GW]', ylabel='million t')

plot_lines(restrict_sysops['Fossil thermal generation'] / 1000, os.path.join(FPATH, 'thermal_generation.pdf'),
           xlim=[18, 0], color=[REFUEL_COLORS[1]], xlabel='Added Capacity of Wind [GW]', ylabel='TWh')

# %% ----- ----- ----- plot wind restriction: changes in cost ----- ----- -----
# system cost, electricity trade balance, system cost net of trade, cost of air pollution (SOx, NOx, PM)
undisturbed_cost = results.loc[idx[scenario, :, :, 36715], idx['AT', ['cost_zonal', 'AnnValueX', 'AnnValueI',
                                                                      'cost_airpol']]]
undisturbed_cost.index = undisturbed_cost.index.droplevel([0, 3])
undisturbed_cost.columns = undisturbed_cost.columns.droplevel(0)
undisturbed_cost['trade_balance'] = undisturbed_cost[['AnnValueX', 'AnnValueI']].sum(axis=1)
undisturbed_cost['syscost_net'] = undisturbed_cost['cost_zonal'] - undisturbed_cost['trade_balance']
undisturbed_cost = undisturbed_cost.drop(['AnnValueX', 'AnnValueI'], axis=1)
undisturbed_cost = undisturbed_cost.rename(columns={'cost_zonal': 'System Cost',
                                                    'trade_balance': 'Electricity trade balance',
                                                    'syscost_net': 'System cost net of trade',
                                                    'cost_airpol': 'Cost of air pollution (SOx, NOx, PM)'})
undisturbed_cost = undisturbed_cost[['System cost net of trade', 'System Cost', 'Cost of air pollution (SOx, NOx, PM)',
                                     'Electricity trade balance']]

restrict_cost = undisturbed_cost.loc[idx[PRICE_CO2, :], :]
restrict_cost.index = restrict_cost.index.droplevel(0)

# plot data
plot_subn(restrict_cost / 1000, os.path.join(FPATH, 'cost.pdf'), xlim=[18, 0], color=REFUEL_COLORS,
          xlabel='Added Capacity of Wind [GW]', ylabel=['million €'])

plot_lines(restrict_cost.loc[:, 'Cost of air pollution (SOx, NOx, PM)'] / 1000,
           os.path.join(FPATH, 'cost_airpollution.pdf'), xlim=[18, 0], color=[REFUEL_COLORS[2]],
           xlabel='Added Capacity of Wind [GW]', ylabel='million €')

# plot_lines(restrict_cost[''] / 1000, os.path.join(FPATH, 'sysops.pdf'), xlim=[18, 0], color=REFUEL_COLORS,
#          xlabel='Added Capacity of Wind [GW]', ylabel=['TWh', 'TWh', 'TWh', 'million t'])

# %% line plot of cost of undisturbed landscapes - baseline capital cost of pv
undisturbed_base = undisturbed_cost[['System cost net of trade',
                                     'Cost of air pollution (SOx, NOx, PM)']].sum(axis=1).unstack(0)
wind_add = results.loc[idx[scenario, :, :, 36715], idx['AT', 'add_r_wind_on']].unstack(1)
wind_add.index = wind_add.index.droplevel([0, 2])

undisturbed_marginal = undisturbed_base.iloc[::-1].diff().divide(wind_add.iloc[::-1].diff().round(8), axis=0) * -1
undisturbed_marginal_share = undisturbed_marginal.copy()
undisturbed_marginal.columns = [rf'CO$_2$ Price: {p} €/t' for p in undisturbed_marginal.columns]

plot_lines(undisturbed_marginal / 1000, os.path.join(FPATH, 'undisturbed_base.pdf'), xlim=[18, 0], ylim=[0, 75],
           xlabel='Added Capacity of Wind [GW]', ylabel='thousand € / MW', color=REFUEL_COLORS)

# %% ------ ----- ----- plot opportunity cost of wind with SHARE of deployment
uplim = results.loc[idx[scenario, PRICE_CO2, :, 36715], idx['AT', 'add_r_wind_on']].max()
# divide index by uplim, delete indices larger than one except for the smallest and set the smallest to 1

lgnd = []

figure, axis = plt.subplots(1, 1, figsize=(8, 5))
axis.set_ylabel('thousand € / MW')
axis.set_xlabel(r'$\phi$')
i = 0
for p in undisturbed_marginal_share.columns:
    oc_by_share = undisturbed_marginal_share.loc[:, p]
    oc_by_share.index = undisturbed_marginal_share.index / wind_add.loc[:, p].max()

    axis.plot(oc_by_share / 1000, color=REFUEL_COLORS[i])
    i = i + 1
    lgnd.append(rf'CO$_2$ Price: {p} €/t')

axis.legend(lgnd)
# axis.set_ylim(ylim)
axis.set_xlim([1, 0])
axis.grid()
# plt.rcParams.update({'font.size': 16})
plt.tight_layout()
plt.savefig(os.path.join(FPATH, 'undisturbed_base_share.pdf'))
plt.close()

# %% line plot of cost of undisturbed landscapes - low capital cost of pv
undisturbed_cost_low = results.loc[idx[scenario, :, :, 16715], idx['AT', ['cost_zonal', 'AnnValueX', 'AnnValueI',
                                                                          'cost_airpol']]]
undisturbed_cost_low.index = undisturbed_cost_low.index.droplevel([0, 3])
undisturbed_cost_low.columns = undisturbed_cost_low.columns.droplevel(0)
undisturbed_cost_low['trade_balance'] = undisturbed_cost_low[['AnnValueX', 'AnnValueI']].sum(axis=1)
undisturbed_cost_low['syscost_net'] = undisturbed_cost_low['cost_zonal'] - undisturbed_cost_low['trade_balance']
undisturbed_cost_low['total_cost'] = undisturbed_cost_low[['syscost_net', 'cost_airpol']].sum(axis=1)

wind_add_low = results.loc[idx[scenario, :, :, 16715], idx['AT', 'add_r_wind_on']].unstack(1)
wind_add_low.index = wind_add_low.index.droplevel([0, 2])

undisturbed_marginal_low = (undisturbed_cost_low['total_cost'].unstack(0).iloc[::-1].diff().divide(
    wind_add_low.iloc[::-1].diff().round(8), axis=0)) * -1
undisturbed_marginal_sens_share = undisturbed_marginal_low.copy()
undisturbed_marginal_low.columns = [rf'CO$_2$ Price: {p} €/t' for p in undisturbed_marginal_low.columns]

plot_lines(undisturbed_marginal_low / 1000, os.path.join(FPATH, 'undisturbed_low.pdf'), xlim=[18, 0], ylim=[0, 75],
           xlabel='Added Capacity of Wind [GW]', ylabel='thousand € / MW', color=REFUEL_COLORS)

# %% ------ ----- ----- plot sensitivity of opportunity cost of wind with SHARE of deployment
# uplim_sens = results.loc[idx['base', PRICE_CO2, :, 16715], idx['AT', 'add_r_wind_on']].max()
# divide index by uplim, delete indices larger than one except for the smallest and set the smallest to 1

lgnd = []

figure, axis = plt.subplots(1, 1, figsize=(8, 5))
axis.set_ylabel('thousand € / MW')
axis.set_xlabel(r'$\phi$')
i = 0
for p in undisturbed_marginal_sens_share.columns:
    oc_by_share = undisturbed_marginal_sens_share.loc[:, p]
    oc_by_share.index = undisturbed_marginal_sens_share.index / wind_add.loc[:, p].max()

    axis.plot(oc_by_share / 1000, color=REFUEL_COLORS[i])
    i = i + 1
    lgnd.append(rf'CO$_2$ Price: {p} €/t')

axis.legend(lgnd)
# axis.set_ylim(ylim)
axis.set_xlim([1, 0])
axis.grid()
# plt.rcParams.update({'font.size': 16})
plt.tight_layout()
plt.savefig(os.path.join(FPATH, 'undisturbed_sens_share.pdf'))
plt.close()

# %% plot sensitivity of optimal res capacity deployment to capital cost of pv
sensitivity = results.loc[idx['pv_sens', [25, 50, 75], 16, :], idx['AT', ['add_r_pv', 'add_r_wind_on']]].copy()
sensitivity.index = sensitivity.index.droplevel([0, 2])
sensitivity.columns = sensitivity.columns.droplevel(0)
sensitivity = sensitivity.unstack(0)
sensitivity.index = np.round(sensitivity.index / ANNUITY_FACTOR / 1000, decimals=2)
sensitivity = sensitivity.rename(mapper={'add_r_pv': 'Solar PV', 'add_r_wind_on': 'Wind Onshore',
                                         0: r'0 €/t CO$_2$', 25: r'25 €/t CO$_2$', 50: r'50 €/t CO$_2$',
                                         75: r'75 €/t CO$_2$', 100: r'100 €/t CO$_2$'}, axis=1)
sensitivity_nrg = sensitivity.copy()
sensitivity.columns = sensitivity.columns.map(', '.join)

plot_lines(sensitivity, os.path.join(FPATH, 'sens_cap.pdf'),
           xlim=[650, 250], ylim=None, xlabel='Capital cost of solar PV [€/kWp]', ylabel='GW', color=RES_COLORS3)

# %% plot sensitivity of optimal res generation to capital cost of pv
sensitivity_nrg.loc[:, idx['Solar PV', :]] = sensitivity_nrg.loc[:, idx['Solar PV', :]] * FLH_PV / 1000
sensitivity_nrg.loc[:, idx['Wind Onshore', :]] = sensitivity_nrg.loc[:, idx['Wind Onshore', :]] * FLH_WINDON / 1000
# sensitivity_nrg.columns = sensitivity_nrg.columns.map(', '.join)

plot_lines(sensitivity_nrg, os.path.join(FPATH, 'sens_nrg.pdf'),
           xlim=[650, 250], ylim=None, xlabel='Capital cost of solar PV [€/kWp]', ylabel='TWh', color=RES_COLORS3)

plot_sublines(sensitivity_nrg, os.path.join(FPATH, 'sens_nrg_sub.pdf'),
              width=2, midx_level=1, subtitle=True, xlim=[650, 250], xlabel='Capital cost of solar PV [€/kWp]',
              ylabel='TWh', color=RES_COLORS2)

# %% plot why wind is not pv
# plot generation profile in one summer week and one winter week
mts = pd.read_csv(os.path.join(cfg.MEDEA_ROOT_DIR, 'data', 'processed', 'medea_regional_timeseries.csv'),
                  parse_dates=True, index_col='DateTime')
mta = mts.loc['2016-01-01':'2016-12-31', ['AT-wind_on-profile', 'AT-pv-profile']]

fig, axs = plt.subplots(2, figsize=(8, 5))
# winter week
axs[0].plot(mta.loc['2016-06-13':'2016-06-19', 'AT-pv-profile'] * 100, linewidth=2, color=RES_COLORS[0])
axs[0].plot(mta.loc['2016-06-13':'2016-06-19', 'AT-wind_on-profile'] * 100, linewidth=2, color=RES_COLORS[2])
axs[0].set_ylabel('% of installed capacity')
axs[0].set_ylim(0, 100)
axs[0].grid()
axs[0].legend(['Solar PV', 'Wind'], loc='upper left')
axs[0].set_title('Summer Week')
# summer week
axs[1].plot(mta.loc['2016-12-05':'2016-12-11', 'AT-pv-profile'] * 100, linewidth=2, color=RES_COLORS[0])
axs[1].plot(mta.loc['2016-12-05':'2016-12-11', 'AT-wind_on-profile'] * 100, linewidth=2, color=RES_COLORS[2])
axs[1].set_ylabel('% of installed capacity')
axs[1].set_ylim(0, 100)
axs[1].grid()
axs[1].legend(['Solar PV', 'Wind'], loc='upper left')
axs[1].set_title('Winter week')

plt.tight_layout()
plt.savefig(os.path.join(FPATH, 'wind_not_pv.pdf'))
plt.close()

# %% data analysis

# % response of capacity additions to \Phi
capa = results.loc[idx[scenario, :, :, 36715], idx['AT', :]]
capa.columns = capa.columns.droplevel(0)
additions = pd.DataFrame()
additions['lig'] = capa.loc[:, capa.columns.str.contains('add_g_lig')].sum(axis=1)
additions['coal'] = capa.loc[:, capa.columns.str.contains('add_g_coal')].sum(axis=1)
additions['oil'] = capa.loc[:, capa.columns.str.contains('add_g_oil')].sum(axis=1)
additions['ng'] = capa.loc[:, capa.columns.str.contains('add_g_ng')].sum(axis=1) - capa.loc[:,
                                                                                   capa.columns.str.contains(
                                                                                       'add_ng_boiler')].sum(axis=1)
additions['bio'] = capa.loc[:, capa.columns.str.contains('add_g_bio')].sum(axis=1)
additions['heatpump'] = capa.loc[:, capa.columns.str.contains('add_g_heatpump')].sum(axis=1)
additions['pv'] = capa.loc[:, capa.columns.str.contains('add_g_pv')].sum(axis=1)
additions['wind'] = capa.loc[:, capa.columns.str.contains('add_g_wind_on')].sum(axis=1)

decomissions = pd.DataFrame()
decomissions['lig'] = capa.loc[:, capa.columns.str.contains('deco_g_lig')].sum(axis=1)
decomissions['coal'] = capa.loc[:, capa.columns.str.contains('deco_g_coal')].sum(axis=1)
decomissions['oil'] = capa.loc[:, capa.columns.str.contains('deco_g_oil')].sum(axis=1)
decomissions['ng'] = capa.loc[:, capa.columns.str.contains('deco_g_ng')].sum(axis=1) - capa.loc[:,
                                                                                       capa.columns.str.contains(
                                                                                           'deco_g_ng_boiler')].sum(
    axis=1)
decomissions['bio'] = capa.loc[:, capa.columns.str.contains('deco_g_bio')].sum(axis=1)
decomissions['heatpump'] = capa.loc[:, capa.columns.str.contains('deco_g_heatpump')].sum(axis=1)
# decomissions['pv'] = capa.loc[:, capa.columns.str.contains('dec_pv')].sum(axis=1)
# decomissions['wind'] = capa.loc[:, capa.columns.str.contains('dec_wind_on')].sum(axis=1)

netadds = additions - decomissions

# %% total capacities (initial + added), and utilisation

# initial capacities
cap_init_at = {
    'ng_stm': 0.13932,
    'ng_stm_chp': 0.606472,
    'ng_cbt_lo': 0.1282346,
    'ng_cbt_lo_chp': 0.27724938,
    'ng_cc_lo': 0.15136,
    'ng_cc_lo_chp': 0.32938,
    'ng_cc_hi_chp': 2.286138,
    'oil_stm': 0.08584,
    'oil_cbt': 0.003915,
    'oil_cbt_chp': 0.04756,
    'oil_cc': 0.0348,
    'bio': 0.354965,
    'bio_chp': 0.369499,
    'ng_boiler_chp': 3.87,
    'heatpump_pth': 0.1
}

ciat = pd.DataFrame.from_dict(cap_init_at, orient='index', columns=[scenario])
ciat.columns.name = 'scenario'
ciat.index.name = 'variable'

caat = capa.loc[:, capa.columns.str.contains('add_g_')].copy()
caat.columns = caat.columns.str.replace('add_g_', '')
caat.columns.name = 'variable'
caat.index = caat.index.rename(['scenario', 'co2price', 'wind_lim', 'pv_cost'])

cdat = capa.loc[:, capa.columns.str.contains('deco_g_')].copy()
cdat.columns = cdat.columns.str.replace('deco_g_', '')
cdat.columns.name = 'variable'
cdat.index = cdat.index.rename(['scenario', 'co2price', 'wind_lim', 'pv_cost'])

ctat = ciat.T + caat - cdat
ctat.dropna(axis=1, how='all', inplace=True)

# heat pump capacity by added wind power for all co2 prices
ctat_htpmp = ctat.loc[:, 'heatpump_pth'].copy()
ctat_htpmp = ctat_htpmp.unstack(1)
ctat_htpmp.index = ctat_htpmp.index.droplevel([0, 2])

plot_lines(ctat_htpmp, os.path.join(FPATH, 'heatpumps.pdf'), xlim=[18, 0], xlabel='wind addition', color=REFUEL_COLORS)

# nat gas fired capacity added for all co2 prices
ngadd = netadds.loc[:, 'ng'].copy()
ngadd = ngadd.unstack(1)
ngadd.index = ngadd.index.droplevel([0, 2])

plot_lines(ngadd, os.path.join(FPATH, 'ng_additions.pdf'), xlim=[18, 0], xlabel='wind addition', color=REFUEL_COLORS)

# %% # generation time series
g_tec = results.loc[idx[scenario, :, :, 36715], idx['AT', :]].copy()
g_tec.columns = g_tec.columns.droplevel(0)
g_tec = g_tec.loc[:, g_tec.columns.str.contains('AnnGByTec_')]
g_tec.columns = g_tec.columns.str.replace('AnnGByTec_', '')
g_tec_mix = pd.MultiIndex.from_tuples(
    [(j.replace('(', '').replace(')', '').replace("'", "").replace(' ', '').split(',')) for j in g_tec.columns])
g_tec.columns = g_tec_mix
# drop heat generation
g_tec = g_tec.loc[:, idx[:, 'el', :]]
g_tec.columns = g_tec.columns.droplevel([1, 2])

util = g_tec / ctat / 8784
util.dropna(axis=1, how='all', inplace=True)

util.loc[idx[scenario, 60, :, 36715], :].plot()
plt.show()

# %% curtailment
curt = results.loc[idx[scenario, :, :, 36715], idx[:, 'AnnCurtail']]
curt.columns = curt.columns.droplevel(1)
curt = curt.unstack(1)
curt.index = curt.index.droplevel([0, 2])

plot_lines(curt.loc[:, idx['AT', :]], os.path.join(FPATH, 'curt_AT.pdf'), xlim=[18, 0], xlabel='wind addition',
           color=REFUEL_COLORS)
plot_lines(curt.loc[:, idx['DE', :]], os.path.join(FPATH, 'curt_DE.pdf'), xlim=[18, 0], xlabel='wind addition',
           color=REFUEL_COLORS)

# %% CO2 emissions
carb = results.loc[idx[scenario, :, :, 36715], idx[:, 'AnnCO2Emissions']]
carb.columns = carb.columns.droplevel(1)
carb = carb.unstack(1)
carb.index = carb.index.droplevel([0, 2])

plot_lines(carb.loc[:, idx['AT', :]], os.path.join(FPATH, 'emissions_AT.pdf'), xlim=[18, 0], xlabel='wind addition',
           color=REFUEL_COLORS)
plot_lines(carb.loc[:, idx['DE', :]], os.path.join(FPATH, 'emissions_DE.pdf'), xlim=[18, 0], xlabel='wind addition',
           color=REFUEL_COLORS)

# %% system cost
syscost = results.loc[idx[scenario, :, :, 36715], idx[:, 'AnnCO2Emissions']]
syscost.columns = syscost.columns.droplevel(1)
syscost = syscost.unstack(1)
syscost.index = syscost.index.droplevel([0, 2])

plot_lines(syscost.loc[:, idx['AT', :]], os.path.join(FPATH, 'syscost_AT.pdf'), xlim=[18, 0], xlabel='wind addition',
           color=REFUEL_COLORS)
plot_lines(syscost.loc[:, idx['DE', :]], os.path.join(FPATH, 'syscost_DE.pdf'), xlim=[18, 0], xlabel='wind addition',
           color=REFUEL_COLORS)

# %% electricity and heat prices
# AvgPriceEl, AvgPriceHt

pel = results.loc[idx[scenario, :, :, 36715], idx[:, 'AvgPriceEl']]
pel.columns = pel.columns.droplevel(1)
pel = pel.unstack(1)
pel.index = pel.index.droplevel([0, 2])

plot_lines(pel.loc[:, idx['AT', :]], os.path.join(FPATH, 'priceel_AT.pdf'), xlim=[18, 0], xlabel='wind addition',
           color=REFUEL_COLORS)
plot_lines(pel.loc[:, idx['DE', :]], os.path.join(FPATH, 'priceel_DE.pdf'), xlim=[18, 0], xlabel='wind addition',
           color=REFUEL_COLORS)

pht = results.loc[idx[scenario, :, :, 36715], idx[:, 'AvgPriceHt']]
pht.columns = pht.columns.droplevel(1)
pht = pht.unstack(1)
pht.index = pht.index.droplevel([0, 2])

plot_lines(pht.loc[:, idx['AT', :]], os.path.join(FPATH, 'priceht_AT.pdf'), xlim=[18, 0], xlabel='wind addition',
           color=REFUEL_COLORS)
plot_lines(pht.loc[:, idx['DE', :]], os.path.join(FPATH, 'priceht_DE.pdf'), xlim=[18, 0], xlabel='wind addition',
           color=REFUEL_COLORS)
