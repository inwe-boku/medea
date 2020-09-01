from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

import config as cfg
from src.tools.visualize_data import plot_lines

# %% settings
APATH = Path(cfg.MEDEA_ROOT_DIR) / 'projects' / 'asparagus'
RPATH = APATH / 'results'
FIGPATH = APATH / 'doc' / 'figures'
REFUEL_COLORS = ['#c72321', '#0d8085', '#f0c220', '#595959', '#3b68f9', '#7794dd']
ANNUITY_FACTOR = 0.05827816
FLH_PV = 1003.36
FLH_WIND = 1983.16
idx = pd.IndexSlice

# %% read scenario results
results = pd.read_csv(Path(RPATH) / 'annual_results.csv', decimal=',', delimiter=';', index_col=[0, 1, 2, 3, 4],
                      header=[0])
results = results.unstack(-1)

results.loc[idx[:], idx['AT', 'cost_zonal_net']] = results.loc[idx[:], idx['AT', 'cost_zonal']] \
                                                   - results.loc[idx[:], idx['AT', 'AnnValueI']] \
                                                   - results.loc[idx[:], idx['AT', 'AnnValueX']] \
                                                   + results.loc[idx[:], idx['AT', 'cost_airpol']]

# %% Calculate Opportunity Cost of Wind Power
mixcols = pd.MultiIndex.from_product([['AT'], ['add_r_wind_on', 'cost_zonal_net', 'oc_wind']])
oc_wind = pd.DataFrame(columns=mixcols)

for scenario in results.index.get_level_values(0).unique():
    for co2_price in results.loc[idx[scenario], :].index.get_level_values(0).unique():
        for pv_cost in results.loc[idx[scenario, co2_price], :].index.get_level_values(1).unique():
            df = results.loc[
                idx[scenario, co2_price, :, pv_cost],
                idx['AT', ['cost_zonal_net', 'add_r_wind_on']]].sort_index(level=2, ascending=False).diff()
            df[idx['AT', 'oc_wind']] = - df[idx['AT', 'cost_zonal_net']] / df[idx['AT', 'add_r_wind_on']]
            oc_wind = oc_wind.append(df)

# %% visualize Opportunity Cost of Wind Power for all CO2 prices
scenario = 'no_bottleneck'  # ['base', 'low_cost', 'must_run', 'no_bottleneck']
co2_price = [0, 25, 50, 75, 100]
pv_cost = 36424

ocw = oc_wind.copy()
ocw.columns = ocw.columns.droplevel(0)
ocw.index = pd.MultiIndex.from_tuples(ocw.index)
ocw.loc[ocw['add_r_wind_on'] > -0.0001, :] = np.nan

oc_costdiff = ocw.loc[idx[scenario, co2_price, :, pv_cost], 'oc_wind'].unstack(1)
oc_costdiff.index = oc_costdiff.index.get_level_values(1)
oc_costdiff = oc_costdiff.add_prefix('CO$_2$ price: ').add_suffix(' €/t')

plot_lines(oc_costdiff / 1000, FIGPATH / f'oc_{scenario}.pdf',
           xlabel='Added Wind Turbine Capacity [GW]', xlim=[14, 0],
           ylabel='\'000 € / MW', ylim=[0, 60], color=REFUEL_COLORS)

# %% scatterplot of unconstrained pv versus wind for various co2 prices
opt_deploy = results.loc[idx['base', :, 16, :], idx['AT', ['add_r_pv', 'add_r_wind_on']]].copy()
opt_deploy.index = opt_deploy.index.get_level_values(1)
opt_deploy.columns = opt_deploy.columns.droplevel(0)
opt_deploy.plot.scatter('add_r_pv', 'add_r_wind_on')
plt.show()

# %% plot various variables against co2 prices
variables = ['AnnCurtail', 'cost_zonal', 'AnnCO2Emissions']

for var in variables:
    misc = results.loc[idx['base', :, 16, :], idx['AT', var]]
    misc.index = misc.index.get_level_values(1)
    misc.plot()
    plt.show()

# %% plot of sensitivity to pv capital cost
senspv = results.loc[idx['pv_sens', :, :, :], idx['AT', :]].copy()
senspv = senspv.loc[idx[:, :, :, :], (senspv != 0).any(axis=0)].dropna(axis=1, how='all')
senspv.columns = senspv.columns.droplevel(0)
senspv.index = pd.MultiIndex.from_tuples(senspv.index.droplevel([0, 2]))
senspv = senspv.unstack(0)
senspv.index = np.round(senspv.index / ANNUITY_FACTOR / 1000, decimals=2)
senspv = senspv.rename(mapper={'add_r_pv': 'Solar PV', 'add_r_wind_on': 'Wind Onshore',
                               0: r'0 €/t CO$_2$', 25: r'25 €/t CO$_2$', 50: r'50 €/t CO$_2$',
                               75: r'75 €/t CO$_2$', 100: r'100 €/t CO$_2$'}, axis=1)
senspv = senspv.loc[:, (senspv != 0).any(axis=0)].dropna(axis=1, how='all')

senspv_nrg = senspv.copy() / 1000
senspv_nrg.loc[:, idx['Solar PV', :]] = senspv.loc[:, idx['Solar PV', :]] * FLH_PV / 1000
senspv_nrg.loc[:, idx['Wind Onshore', :]] = senspv.loc[:, idx['Wind Onshore', :]] * FLH_WIND / 1000

var = ['Solar PV', 'Wind Onshore']
price_co2 = ['25 €/t CO$_2$', '50 €/t CO$_2$', '75 €/t CO$_2$', '100 €/t CO$_2$']  # '0 €/t CO$_2$',

# plot in terms of power
for v in var:
    mix = pd.MultiIndex.from_product([[v], price_co2])
    dfp = senspv.loc[:, idx[mix]]
    dfp.columns = dfp.columns.droplevel(0)
    plot_lines(dfp, FIGPATH / f'S_PVCost_P_{v}.pdf',
               xlabel='Capital Cost of PV [€/kWp]', xlim=[870, 250], color=REFUEL_COLORS)

# plot in terms of energy
for v in var:
    mix = pd.MultiIndex.from_product([[v], price_co2])
    dfp = senspv_nrg.loc[:, idx[mix]]
    dfp.columns = dfp.columns.droplevel(0)
    plot_lines(dfp, FIGPATH / f'S_PVCost_E_{v}.pdf',
               xlabel='Capital Cost of PV [€/kWp]', ylabel='TWh per annum', xlim=[870, 250], color=REFUEL_COLORS)

# plot total energy (wind + pv)
for p in price_co2:
    senspv_nrg['Total Energy', p] = \
        senspv_nrg.loc[:, idx[pd.MultiIndex.from_product([var, [p]])]].sum(axis=1)

plot_lines(senspv_nrg['Total Energy'], FIGPATH / f'S_PVCost_E_tot.pdf',
           xlabel='Capital Cost of PV [€/kWp]', ylabel='TWh per annum', xlim=[870, 250], color=REFUEL_COLORS)

# %% plot pv capital cost sensitivity as share of rooftop / open-space installations versus installed capacity in optimum
# (c-280) / (830-280) = a  with a ... share rooftop
senspv_nrg_share = senspv_nrg.copy()
senspv_nrg_share.index = (senspv_nrg_share.index - 380) / (870 - 380) * 100

for v in var:
    mix = pd.MultiIndex.from_product([[v], price_co2])
    dfp = senspv_nrg_share.loc[:, idx[mix]]
    dfp.columns = dfp.columns.droplevel(0)
    plot_lines(dfp, FIGPATH / f'S_PVCost_E_pct_{v}.pdf',
               xlabel='Share of rooftop PV in total PV installations (remainder is open-space PV) [%]',
               ylabel='TWh per annum', xlim=[100, 0], color=REFUEL_COLORS)

# %% plot emissions versus PV / wind restriction
emis = results.loc[idx['base', :], idx['AT', 'AnnCO2Emissions']] / 1000
emis.index = emis.index.droplevel([0, -1])
emis = emis.unstack(0)

plot_lines(emis, FIGPATH / 'Emissions.pdf',
           color=REFUEL_COLORS, xlim=[14, 0],
           xlabel='Installed Wind Power Capacity [GW]',
           ylabel='Annual CO$_2$ Emissions from Fuel Combustion [mn t]')

# %% further plots:
# * sensitivity to transmission capacity
senstrans = ocw.loc[idx['no_bottleneck'], 'oc_wind'].unstack(0)
senstrans.index = senstrans.index.droplevel(1)
plot_lines(senstrans, FIGPATH / 'sensitivity_transmissions.pdf',
           xlabel='Installed wind capacity [GW]', ylabel='Cost [EUR]',
           xlim=[14, 0], color=REFUEL_COLORS)
# * sensitivity to must-run assumption
sensmrun = ocw.loc[idx['must_run'], 'oc_wind'].unstack(0)
sensmrun.index = sensmrun.index.droplevel(1)
plot_lines(sensmrun, FIGPATH / 'sensitivity_mustrun.pdf',
           xlabel='Installed wind capacity [GW]', ylabel='Cost [EUR]',
           xlim=[14, 0], color=REFUEL_COLORS)
# * policy effect compared to no policy / co2-pricing
# --> what to do here?

# %% Decomposition of system cost
# * is it possible to decompose the increase in system cost in different parts?
# * in medea, cost-parts get calculated separately. Look at these!
# plot investment cost versus wind / pv installed capacity

# %% MAKE DECOMPOSITION OF EMISSION EFFECT
# compoments of change in emissions:
# - demand increase
# - change in co2 price
# - addition of RET / policy
# -
# * run no_policy without additional demand
# * run no_policy with additional demand and compare to get demand effect cet par.
# * run policy with additional demand and compare to no policy with additional demand to get policy effect cet. par.
# * repeat for co2 prices of 25, 50, 75, 100 -- 12 runs in total
#


# %% MAKE SEASONAL ANALYSIS -- show where additional cost of PV come from
# * plot seasonal patterns of ror, consumption, pv, wind
cols = ['AT-wind_on-generation', 'AT-ror-generation', 'AT-pv-generation', 'AT-power-load']
seas = pd.read_csv(Path(cfg.MEDEA_ROOT_DIR) / 'data' / 'processed' / 'medea_regional_timeseries.csv', index_col=[0])
seas.index = pd.to_datetime(seas.index)
seas = seas.loc['2016', cols]
seasm = seas.resample('M', label='left').mean() / seas.mean()
seasm = seasm.rename(mapper={'AT-pv-generation': 'solar PV', 'AT-wind_on-generation': 'wind onshore',
                             'AT-ror-generation': 'run-of-river', 'AT-power-load': 'electricity consumption'}, axis=1)
plot_lines(seasm, FIGPATH / 'seasonal.pdf', x_date_format='months', color=REFUEL_COLORS)
