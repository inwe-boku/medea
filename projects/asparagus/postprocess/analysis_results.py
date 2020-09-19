from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy.stats import pearsonr

import config as cfg
from src.tools.data_processing import medea_path
from src.tools.visualize_data import plot_lines

# %% settings
APATH = medea_path('projects', 'asparagus')
RPATH = APATH / 'results'
FIGPATH = APATH / 'doc' / 'figures'
REFUEL_COLORS = ['#c72321', '#0d8085', '#f0c220', '#595959', '#3b68f9', '#7794dd']
ANNUITY_FACTOR = 0.05827816
FLH_PV = 1003.36
FLH_WIND = 1983.16
idx = pd.IndexSlice

# %% read scenario results
results = pd.read_csv(RPATH / 'annual_results.csv', decimal=',', delimiter=';', index_col=[0, 1, 2, 3, 4],
                      header=[0])
results = results.unstack(-1)

results.loc[idx[:], idx['AT', 'cost_zonal_net']] = results.loc[idx[:], idx['AT', 'cost_zonal']] \
                                                   - results.loc[idx[:], idx['AT', 'AnnValueI']] \
                                                   - results.loc[idx[:], idx['AT', 'AnnValueX']] \
                                                   + results.loc[idx[:], idx['AT', 'cost_airpol']]

# drop columns with only zero or nan
results[results == 0] = np.nan
results.dropna(axis=1, how='all', inplace=True)
results.fillna(0, inplace=True)

# Calculate derived results
results.loc[:, idx['AT', 'AnnGFossil']] = results.loc[:, idx['AT', 'AnnG_el']] - \
                                          results.loc[:, idx['AT', 'AnnGBiomass']]
results.loc[:, idx['AT', 'AnnG_htFromEl']] = results.loc[:, idx['AT',
                                                                'AnnGByTec_(\'eboi_pth\', \'ht\', \'Power\')']] + \
                                             results.loc[:, idx['AT',
                                                                'AnnGByTec_(\'heatpump_pth\', \'ht\', \'Power\')']]
results.loc[:, idx['AT', 'AnnValueXNet']] = results.loc[:, idx['AT', 'AnnValueX']] + \
                                            results.loc[:, idx['AT', 'AnnValueI']]

# %% plot of storage operation
st_op = results.loc[idx['base', :, :, 36424], idx['AT', 'AnnSOut']].copy()
st_op = st_op.unstack([1])
st_op.index = st_op.index.get_level_values(1)
st_op.plot()
plt.show()

# %% plot of electricity trade
nxnrg = results.loc[idx['base', :, :, 36424], idx['DE', 'AnnX']].copy()
nxnrg = nxnrg.unstack([1])
nxnrg.index = nxnrg.index.get_level_values(1)
nxnrg.plot()
plt.show()

# nxval = results.loc[idx['base', :, :, 36424], idx['AT', ['AnnValueX', 'AnnValueI']]].copy().sum(axis=1)
nxval = results.loc[idx['base', :, :, 36424], idx['AT', ['AnnValueI']]].copy()
nxval = nxval.unstack([1])
nxval.index = nxval.index.get_level_values(1)
nxval.plot()
plt.show()

# %% plot total installed fossil generation capacities
foscap = results.loc[
    idx['base', :, :, 36424], idx['AT', results.columns.get_level_values(1).str.contains('add_g_ng')]].copy().sum(
    axis=1)
foscap = foscap.unstack([1])
foscap.index = foscap.index.get_level_values(1)
# foscap.plot()
# plt.show()

fosdec = results.loc[
    idx['base', :, :, 36424], idx['AT', results.columns.get_level_values(1).str.contains('deco_g_ng')]].copy().sum(
    axis=1)
fosdec = fosdec.unstack([1])
fosdec.index = fosdec.index.get_level_values(1)
# fosdec.plot()
# plt.show()

fosnet = foscap - fosdec
fosnet.plot()
plt.show()

# %% system cost decomposition
coco = ['CostCO2', 'CostFuel', 'CostOMG', 'CostOMR', 'cost_invest_g', 'cost_invest_r']
sysco = results.loc[idx['base', :, :, 36424], idx['AT', coco]].copy()
sysco.index = sysco.index.droplevel([0, 3])
sysco.columns = sysco.columns.get_level_values(1)

prices = sysco.index.get_level_values(0).unique()
for p in prices:
    sysco.loc[idx[p, :], :].plot()
    plt.show()
# sysco.plot()
# plt.show()

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
scenario = ['base', 'low_cost', 'must_run', 'no_bottleneck']
co2_price = [25, 50, 75]
pv_cost = 36424

ocw = oc_wind.copy()
ocw.columns = ocw.columns.droplevel(0)
ocw.index = pd.MultiIndex.from_tuples(ocw.index)
ocw.loc[ocw['add_r_wind_on'] > -0.0001, :] = np.nan

oc_costdiff = ocw.loc[idx[scenario, co2_price, :, pv_cost], 'oc_wind'].unstack(1)
oc_costdiff = oc_costdiff.unstack(0)
oc_costdiff.index = oc_costdiff.index.get_level_values(0)

# oc_mean = oc_costdiff.loc[:, idx[:, 'base']].mean(axis=1)
# (oc_mean.loc[0] - oc_mean.loc[14])/14

for sc in scenario:
    oc_cd = oc_costdiff.loc[:, idx[:, sc]].copy()
    oc_cd.columns = oc_cd.columns.get_level_values(0)
    oc_cd = oc_cd.add_prefix('CO$_2$ price: ').add_suffix(' €/t')

    plot_lines(oc_cd / 1000, FIGPATH / f'oc_{sc}.pdf',
               xlabel='Added Wind Turbine Capacity [GW]', xlim=[14, 0],
               ylabel='\'000 € / MW', ylim=[0, 60], color=REFUEL_COLORS)

# %% plot opportunity cost of wind power at low PV overnight cost
scenario = ['low_cost']  # ['base', 'low_cost', 'must_run', 'no_bottleneck']
co2_price = [25, 50, 75]
pv_cost = [29285, 22146]  # 36424

ocwl = oc_wind.copy()
ocwl.columns = ocwl.columns.droplevel(0)
ocwl.index = pd.MultiIndex.from_tuples(ocwl.index)
ocwl.loc[ocwl['add_r_wind_on'] > -0.0001, :] = np.nan

oc_cdl = ocwl.loc[idx[scenario, co2_price, :, pv_cost], 'oc_wind'].unstack(1)
oc_cdl = oc_cdl.unstack(2)
oc_cdl.index = oc_cdl.index.get_level_values(1)

for pvc in pv_cost:
    oc_cdlp = oc_cdl.loc[:, idx[:, pvc]].copy()
    oc_cdlp.columns = oc_cdlp.columns.get_level_values(0)
    oc_cdlp = oc_cdlp.add_prefix('CO$_2$ price: ').add_suffix(' €/t')

    plot_lines(oc_cdlp / 1000, FIGPATH / f'oc_low_{pvc}.pdf',
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
               xlabel='Capital Cost of PV [€/kWp]', xlim=[650, 250],
               ylabel='Added Wind Energy Converter Capacity [GW]', color=REFUEL_COLORS)

# plot in terms of energy
for v in var:
    mix = pd.MultiIndex.from_product([[v], price_co2])
    dfp = senspv_nrg.loc[:, idx[mix]]
    dfp.columns = dfp.columns.droplevel(0)
    plot_lines(dfp, FIGPATH / f'S_PVCost_E_{v}.pdf',
               xlabel='Capital Cost of PV [€/kWp]', ylabel='TWh per annum', xlim=[650, 250], color=REFUEL_COLORS)

# plot total energy (wind + pv)
for p in price_co2:
    senspv_nrg['Total Energy', p] = \
        senspv_nrg.loc[:, idx[pd.MultiIndex.from_product([var, [p]])]].sum(axis=1)

plot_lines(senspv_nrg['Total Energy'], FIGPATH / f'S_PVCost_E_tot.pdf',
           xlabel='Capital Cost of PV [€/kWp]', ylabel='TWh per annum', xlim=[650, 250], color=REFUEL_COLORS)

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

# %% calculate opportunity cost for low cost of pv


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


# %% ANALYSIS OF INTERMITTENT GENERATION -- show where additional cost of PV come from
# read data
cols = ['AT-wind_on-generation', 'AT-ror-generation', 'AT-pv-generation', 'AT-power-load']
itm = pd.read_csv(Path(cfg.MEDEA_ROOT_DIR) / 'data' / 'processed' / 'medea_regional_timeseries.csv', index_col=[0])
itm.index = pd.to_datetime(itm.index)
intmit = itm.copy()
itm = itm.loc['2016', cols]

# * calculate variance of intermittent generation for base case and constrained wind power expansion
varix = ['base', 'wind8', 'wind4', 'wind0']
caps = pd.DataFrame(columns=cols[0:3], index=varix)
caps['AT-ror-generation'] = 6.7
caps.loc['base', 'AT-pv-generation'] = 1.096 + 0.698
caps.loc['wind8', 'AT-pv-generation'] = 1.096 + 9.259
caps.loc['wind4', 'AT-pv-generation'] = 1.096 + 17.161
caps.loc['wind0', 'AT-pv-generation'] = 1.096 + 25.233
caps.loc['base', 'AT-wind_on-generation'] = 2.649 + 12.347
caps.loc['wind8', 'AT-wind_on-generation'] = 2.649 + 8
caps.loc['wind4', 'AT-wind_on-generation'] = 2.649 + 4
caps.loc['wind0', 'AT-wind_on-generation'] = 2.649

#
itmvar = pd.DataFrame(index=varix, columns=['Variance'])
for i in varix:
    itmvar.loc[i, 'Variance'] = (itm * caps.loc[i, :]).sum(axis=1).var()

# * plot seasonal patterns of ror, consumption, pv, wind
seasm = itm.resample('M', label='left').mean() / itm.mean()
seasm = seasm.rename(mapper={'AT-pv-generation': 'solar PV', 'AT-wind_on-generation': 'wind onshore',
                             'AT-ror-generation': 'run-of-river', 'AT-power-load': 'electricity consumption'}, axis=1)
plot_lines(seasm, FIGPATH / 'seasonal.pdf', x_date_format='months', color=REFUEL_COLORS)

# %% ANALYSIS OF HOURLY TRADE
# read data
trd = pd.read_csv(medea_path('projects', 'asparagus', 'results', 'hourly_results.csv'), sep=';', decimal=',',
                  index_col=[0, 1, 2, 3, 4], header=[0, 1])

# exports x and imports i for baseline scenario
cors = pd.DataFrame(index=range(100, -1, -25), columns=pd.MultiIndex.from_product([[0, 16], ['xw', 'xp', 'i']]))
for p_co2 in range(100, -1, -25):
    for wlim in [16, 0]:
        trdat = pd.DataFrame(columns=['x', 'i'])
        trdat['x'] = trd.loc[idx['base', p_co2, wlim, 36424, :], idx['AT', 'DE']].copy()
        trdat.loc[trdat['x'] < 0, 'x'] = 0

        trdat['i'] = trd.loc[idx['base', p_co2, wlim, 36424, :], idx['AT', 'DE']].copy()
        trdat.loc[trdat['i'] > 0, 'i'] = 0
        trdat.loc[trdat['i'] < 0, 'i'] = -trdat.loc[trdat['i'] < 0, 'i']

        # calculate correlations with intermittent generation
        cri = pearsonr(trdat['i'], intmit.loc['2016', 'DE-pv-generation'])
        crxw = pearsonr(trdat['x'], intmit.loc['2016', 'AT-wind_on-generation'])
        crxp = pearsonr(trdat['x'], intmit.loc['2016', 'AT-pv-generation'])
        cors.loc[p_co2, idx[wlim, 'i']] = cri[0]
        cors.loc[p_co2, idx[wlim, 'xw']] = crxw[0]
        cors.loc[p_co2, idx[wlim, 'xp']] = crxp[0]

# When no wind installed, exports positively correlated with PV. --> What happens to per UNIT VALUE of exports?
x = trd.loc[idx['base', :, :, 36424, :], idx['AT', 'DE']].copy()
x[x < 0] = 0
xann = x.groupby(level=[1, 2]).sum()
xann.index.names = ['pcarb', 'wlim']

xval = results.loc[idx['base', :, :, 36424], idx['AT', 'AnnValueX']]
xval.index.names = ['scenario', 'pcarb', 'wlim', 'cpv']

xunitval = xval / xann
xunitval = xunitval.unstack(1)
xunitval.index = xunitval.index.get_level_values(1)
