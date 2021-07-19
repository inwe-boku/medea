from pathlib import Path

import matplotlib.pylab as pylab
import matplotlib.pyplot as plt
import numpy as np
import numpy.polynomial.polynomial as poly
import numpy_financial as npf
import pandas as pd
import statsmodels.api as sm

import config as cfg
from src.utils.data_processing import medea_path
from src.utils.visualize_data import plot_lines

# TODO: create /asparagus/doc/figures-subfolder before saving figures
# TODO: Plots of first differrences (e.g. oc of wind) need to have their x-axis adjusted (shift to mean of adjacent categories)
# TODO: plot sensitivity as scatters of baseline versus sensivitiy scenario plot

# %% settings
params = {
    'legend.fontsize': 9,
    'axes.labelsize': 9,
    'axes.titlesize': 10,
    'xtick.labelsize': 9,
    'ytick.labelsize': 9}
pylab.rcParams.update(params)

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

results.loc[idx[:], idx['DE', 'cost_zonal_net']] = results.loc[idx[:], idx['DE', 'cost_zonal']] \
                                                   - results.loc[idx[:], idx['DE', 'AnnValueI']] \
                                                   - results.loc[idx[:], idx['DE', 'AnnValueX']] \
                                                   + results.loc[idx[:], idx['DE', 'cost_airpol']]

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
results.loc[:, idx['AT', 'AnnX']] = results.loc[:, idx['DE', 'AnnX']]

itm = pd.read_csv(Path(cfg.MEDEA_ROOT_DIR) / 'data' / 'processed' / 'medea_regional_timeseries.csv', index_col=[0])
itm.index = pd.to_datetime(itm.index)

"""
# %% Figure 1: horizontal bar plot of cost in unconstrained baseline
px_height = 375
px_width = 960
margin_topbottom = 0.25
margin_leftright = 0.1
dpi = 200

colors = ['#7a6952', '#f0c220', '#0d8085', '#c72321']

pco2 = 25
region = 'AT'
scenario = 'base'

costcomps = ['cost_invest_g', 'cost_invest_r', 'cost_invest_sv', 'CostCO2', 'CostFuel', 'CostOMG',
             'CostOMR', 'AnnValueI', 'AnnValueX']

coba = results.loc[idx[scenario, pco2, 16, :], idx[region, costcomps]]
coba.index = coba.index.droplevel([0, 3])
coba.columns = coba.columns.droplevel(0)

coba['Invest'] = coba.loc[:, ['cost_invest_r', 'cost_invest_g', 'cost_invest_sv']].sum(axis=1)
coba['O&M'] = coba.loc[:, ['CostOMR', 'CostOMG']].sum(axis=1)
coba['Fuel & CO$_2$'] = coba.loc[:, ['CostCO2', 'CostFuel']].sum(axis=1)
coba['Trade Balance'] = - coba.loc[:, ['AnnValueX', 'AnnValueI']].sum(axis=1)
coba = coba.reindex(coba.index.levels[1][::-1], level=1, axis=0)

ploba = coba.loc[idx[pco2, :], ['Invest', 'O&M', 'Fuel & CO$_2$', 'Trade Balance']] / 1000
ploba.index = ploba.index.droplevel(0)

ploba_plus = ploba.dropna(axis=0).copy()
ploba_plus[ploba_plus < 0] = 0
ploba_minus = ploba.dropna(axis=0).copy()
ploba_minus[ploba_minus > 0] = 0

fig_height = px_height / dpi / (1 - 2 * margin_topbottom)
fig_width = px_width / dpi / (1 - 2 * margin_leftright)

cumval = 0
cumval_minus = 0
fig, ax = plt.subplots(1, 1, figsize=(fig_width, fig_height))

i = 0
for col in ['Fuel & CO$_2$', 'Invest', 'O&M', 'Trade Balance']:
    ax.barh(ploba_plus.index, ploba_plus[col], left=cumval, label=col, color=colors[i])
    ax.barh(ploba_minus.index, ploba_minus[col], left=cumval_minus, color=colors[i])
    cumval = cumval + ploba_plus[col]
    cumval_minus = cumval_minus + ploba_minus[col]
    i = i + 1
ax.set_xlim([-1000, 3000])
ax.set_ylim([15.4, 16.9])
ax.set_yticks([])
ax.set_xlabel('Cost [Mio EUR]')
plt.legend()
plt.grid()
ax.set_axisbelow(True)
plt.tight_layout()
plt.savefig(APATH / 'doc' / 'figures' / 'cost_baseline.pdf', dpi=dpi)
plt.close()
"""
# %% Figure 2: figure of seasonal variation in ror, wind_on, pv, cons_el
# transform data
cols = ['AT-wind_on-generation', 'AT-ror-generation', 'AT-pv-generation', 'AT-power-load']
seasm = itm.loc['2016', cols].resample('M', label='left').mean() / itm.loc['2016', cols].mean()
seasm = seasm.rename(mapper={'AT-pv-generation': 'Solar PV', 'AT-wind_on-generation': 'Wind onshore',
                             'AT-ror-generation': 'Run-of-river', 'AT-power-load': 'Electricity consumption'}, axis=1)
# plot figure
plot_lines(seasm, FIGPATH / 'seasonal.pdf', ylabel='normalized generation / consumption',
           x_ax_date_format='%b', color=REFUEL_COLORS)

# %% Figure 3 & 7: change in net system cost - baseline and sensitivity to transmission capacity
pco2 = 25
region = 'AT'
scenario = ['base', 'no_bottleneck']

costcomps = ['cost_invest_g', 'cost_invest_r', 'cost_invest_sv', 'CostCO2', 'CostFuel', 'CostOMG',
             'CostOMR', 'AnnValueI', 'AnnValueX']

for scen in scenario:
    coco = results.loc[idx[scen, :, :, :], idx[region, costcomps]]
    coco.index = coco.index.droplevel([0, 3])
    coco.columns = coco.columns.droplevel(0)

    coco['Invest'] = coco.loc[:, ['cost_invest_r', 'cost_invest_g', 'cost_invest_sv']].sum(axis=1)
    coco['O&M'] = coco.loc[:, ['CostOMR', 'CostOMG']].sum(axis=1)
    coco['Fuel & CO$_2$'] = coco.loc[:, ['CostCO2', 'CostFuel']].sum(axis=1)
    coco['Trade Balance'] = - coco.loc[:, ['AnnValueX', 'AnnValueI']].sum(axis=1)
    coco = coco.iloc[::-1]  # coco.reindex(coco.index.levels[1][::-1], level=1, axis=0)

    toco = coco.loc[idx[pco2, :], ['Invest', 'O&M', 'Fuel & CO$_2$', 'Trade Balance']].sum(axis=1) / 1000

    ploco = coco.loc[idx[pco2, :], ['Invest', 'O&M', 'Fuel & CO$_2$', 'Trade Balance']] / 1000
    ploco.index = ploco.index.droplevel(0)
    ploco.index = ploco.index + 1
    ploco = ploco.diff()

    ploco_plus = ploco.dropna(axis=0).copy()
    ploco_plus[ploco_plus < 0] = 0
    ploco_minus = ploco.dropna(axis=0).copy()
    ploco_minus[ploco_minus > 0] = 0

    # plotting
    px_height = 375
    px_width = 960
    margin_topbottom = 0.25
    margin_leftright = 0.1
    dpi = 200
    fig_height = px_height / dpi / (1 - 2 * margin_topbottom)
    fig_width = px_width / dpi / (1 - 2 * margin_leftright)

    # colors = ['#0d8085', '#f0c220', '#7a6952', '#c72321']
    colors = ['#7a6952', '#f0c220', '#0d8085', '#c72321']

    cumval = 0
    cumval_minus = 0
    fig, ax = plt.subplots(1, 1, figsize=(fig_width, fig_height))
    i = 0
    for col in ['Fuel & CO$_2$', 'Invest', 'O&M', 'Trade Balance']:  # ploco_plus.columns:
        ax.bar(ploco_plus.index, ploco_plus[col], bottom=cumval, label=col, color=colors[i])
        ax.bar(ploco_minus.index, ploco_minus[col], bottom=cumval_minus, color=colors[i])
        cumval = cumval + ploco_plus[col]
        cumval_minus = cumval_minus + ploco_minus[col]
        i = i + 1
    ax.set_xlim([12, 0])
    ax.set_ylim([-20, 70])
    ax.set_ylabel('Change in Net System Cost [Mio EUR]')
    ax.set_xlabel('Added Capacity of Wind Turbines [GW]')
    plt.legend()
    plt.grid()
    ax.set_axisbelow(True)
    plt.tight_layout()
    plt.savefig(APATH / 'doc' / 'figures' / f'cost_components_{scen}_{pco2}.pdf', dpi=dpi)
    plt.close()

# %% figure showing renewable generation to illustrate when policy is binding
"""
sc = 'base'
rgen = results.loc[idx[sc, :, :, :], idx['AT', ['AnnR', 'AnnGBiomass', 'AnnSIn', 'AnnSOut']]]
rgen.columns = rgen.columns.get_level_values(1)
rgen['GRE'] = rgen['AnnR'] + rgen['AnnGBiomass'] + rgen['AnnSOut'] - rgen['AnnSIn'] * 0.81
rgen = rgen['GRE'].unstack(1)
rgen.index = rgen.index.get_level_values(1)
rgen = rgen.add_prefix('CO$_2$ price: ').add_suffix(' €/t')

plot_lines(rgen / 1000, FIGPATH / f'rgen_{sc}.pdf',
           xlabel='Added Capacity of Wind Turbines [GW]', xlim=[14, 0],
           ylabel='Renewable Electricity Generation [TWh/a]', ylim=[70, 90], color=REFUEL_COLORS)
"""

# %% figure showing electricity generation, net exports, fossil generation, co2 emissions in baseline for all wind caps
"""
scn = 'base'
pco2 = 25

plot_cols = ['AnnGFossil', 'AnnX', 'AnnCO2Emissions', 'AnnCurtail', 'add_r_wind_on']
sysop = results.loc[idx[scn, pco2, :, 36424],
                    idx[:, plot_cols]]
rnm = {'AnnCurtail': 'Curtailed Electricity', 'AnnGFossil': 'Fossil Electricity Generation', 'AnnX': 'Net Exports',
       'AnnCO2Emissions': 'CO$_2$ Emissions'}
sysop.rename(columns=rnm, inplace=True)
sysop.set_index(('AT', 'add_r_wind_on'), inplace=True)
sysop.drop(('DE', 'add_r_wind_on'), axis=1, inplace=True)
sysop = sysop.iloc[0:-1, :]

sysop.loc[:, idx['Total', 'Fossil Electricity Generation']] = sysop.loc[:, idx[:, 'Fossil Electricity Generation']].sum(
    axis=1)
sysop.loc[:, idx['Total', 'CO$_2$ Emissions']] = sysop.loc[:, idx[:, 'CO$_2$ Emissions']].sum(axis=1)
sysop.loc[:, idx['Total', 'Curtailed Electricity']] = sysop.loc[:, idx[:, 'Curtailed Electricity']].sum(axis=1)
sysop.loc[:, idx['Total', 'Net Exports']] = sysop.loc[:, idx[:, 'Net Exports']].sum(axis=1)

col_order = ['Fossil Electricity Generation', 'Net Exports', 'CO$_2$ Emissions', 'Curtailed Electricity']

for reg in sysop.columns.get_level_values(0).unique():
    df = sysop.loc[:, idx[reg, :]]
    df.columns = df.columns.get_level_values(1)
    df = df[col_order]
    plot_subn(df / 1000, FIGPATH / f'sysops_{scn}_{pco2}_{reg}.pdf', ylabel=['TWh', 'TWh', 'million t', 'TWh'],
              y_ax_fixed_spacing=[True, True, False, True], xlim=[12, 0],
              xlabel='Added Capacity of Wind Turbines [GW]', color=REFUEL_COLORS)
"""
# %% Figure 5: figure showing the opportunity cost of wind power
# Calculate Opportunity Cost of Wind Power
oc_wind = pd.DataFrame(columns=pd.MultiIndex.from_product([['AT'], ['add_r_wind_on', 'cost_zonal_net', 'oc_wind']]))
for scn in results.index.get_level_values(0).unique():
    for co2_price in results.loc[idx[scn], :].index.get_level_values(0).unique():
        for pv_cost in results.loc[idx[scn, co2_price], :].index.get_level_values(1).unique():
            df = results.loc[
                idx[scn, co2_price, :, pv_cost],
                idx['AT', ['cost_zonal_net', 'add_r_wind_on']]].sort_index(level=2, ascending=False).diff()
            df[idx['AT', 'oc_wind']] = - df[idx['AT', 'cost_zonal_net']] / df[idx['AT', 'add_r_wind_on']]
            oc_wind = oc_wind.append(df)

# transform data
ocw = oc_wind.copy()
ocw.columns = ocw.columns.droplevel(0)
ocw.index = pd.MultiIndex.from_tuples(ocw.index)
ocw.loc[ocw['add_r_wind_on'] > -0.0001, :] = np.nan

# select figure properties
scenario = ['base']  # 'base', 'low_cost', 'must_run', 'no_bottleneck']
co2_price = [0, 25, 50, 75, 100]  # 0, 25, 50, 75, 100
pv_cost = 36424  # 36424, 32530

oc_costdiff = ocw.loc[idx[scenario, co2_price, :, pv_cost], 'oc_wind'].unstack(1)
oc_costdiff = oc_costdiff.unstack(0)
oc_costdiff.index = oc_costdiff.index.get_level_values(0)
oc_costdiff.index = oc_costdiff.index + 1

# plot figures
for sc in scenario:
    oc_cd = oc_costdiff.loc[:, idx[:, sc]].copy()
    oc_cd.columns = oc_cd.columns.get_level_values(0)
    oc_cd = oc_cd.add_prefix('CO$_2$ price: ').add_suffix(' €/t')

    plot_lines(oc_cd / 1000, FIGPATH / f'oc_{sc}.pdf',
               xlabel='Added Capacity of Wind Turbines [GW]', xlim=[16, 0],
               ylabel='\'000 € / MW', ylim=[-5, 50], color=REFUEL_COLORS)

# %% OLS to oc_costdiff
X = oc_costdiff.copy()
X.columns = X.columns.get_level_values(0)
X = X.stack()
X.index = X.index.droplevel(1)

# X = sm.add_constant(X)
# y = X.index
# model = sm.OLS(y, X)

y = X
X = sm.add_constant(X.index)
model = sm.OLS(y, X)

regres = model.fit()
print(regres.summary())

ypred = (regres.params * [1, 5.05]).sum()

# lifetime cost of 3.5 MW windturbine
discount_rate = 0.05
lifetime = 30
capacity = 3.5
ypred = 18643.4
npv_ocw = npf.npv(discount_rate, [ypred * capacity] * lifetime)

# %% Figure 6: scatter plot of opportunity cost in sensitivity scenarios & cubic fit
scenario = ['base', 'no_bottleneck', 'low_cost']
scenario_dict = {'base': 'Baseline', 'no_bottleneck': 'No Transmission Bottleneck',
                 'low_cost': 'Low Capital Cost of PV'}
ocws = ocw.unstack(0).copy()
ocws = ocws.loc[:, idx['oc_wind', scenario]]
ocws.dropna(how='all', axis=0, inplace=True)
ocws = ocws.groupby(level=[0, 1]).sum()
ocws[ocws == 0] = np.nan
ocws.columns = ocws.columns.droplevel(0)
ocws.rename(columns=scenario_dict, inplace=True)
ocws.index = ocws.index.set_levels(ocws.index.levels[1] + 1, level=1)

colorado = ["#861719", "#ba9f7c", "#f0c320"]  # "#fbd7a9",  "#7a6952", "#19484c", "#6e9b9e", "#af8f19",
line_width = [3, 2, 1.5]
i = 0
# scatter plot
fig, ax = plt.subplots(nrows=1, ncols=1)
for s in ocws.columns:
    x_new = np.linspace(ocws[s].dropna().index.get_level_values(1).min(),
                        ocws[s].dropna().index.get_level_values(1).max(), num=30)

    ax.scatter(ocws[s].dropna().index.get_level_values(1), ocws[s].dropna() / 1000, s=0.75, color=colorado[i])
    coefs = poly.polyfit(ocws[s].dropna().index.get_level_values(1), ocws[s].dropna() / 1000, 3)
    ffit = poly.polyval(x_new, coefs)
    ax.plot(x_new, ffit, color=colorado[i], linewidth=line_width[i])
    i = i + 1
    ax.set_ylabel('\'000 € / MW')
    ax.set_xlabel('Added Capacity of Wind Turbines [GW]')
    ax.legend(ocws.columns)
    ax.set_xlim([16, 0])
    ax.set_ylim([0, 50])
    ax.grid()
    plt.tight_layout()
plt.savefig(FIGPATH / f'Sensitivities.pdf')

# %% OLS to oc_costdiff in sensitivity scenario
X = oc_costdiff.copy()
X.columns = X.columns.get_level_values(0)
X = X.stack()
X.index = X.index.droplevel(1)

# X = sm.add_constant(X)
# y = X.index
# model = sm.OLS(y, X)

y = X
X = sm.add_constant(X.index)
model = sm.OLS(y, X)

regres = model.fit()
print(regres.summary())

ypred = (regres.params * [1, 5.05]).sum()

# lifetime cost of 3.5 MW windturbine
discount_rate = 0.05
lifetime = 30
capacity = 3.5

npv_ocw = npf.npv(discount_rate, [ypred * capacity] * lifetime)

# %% Figure 7: figure showing the optimal deployment of wind power conditional on cost of pv
senspv = results.loc[idx['pv_sens', :, :, :], idx['AT', ['add_r_pv', 'add_r_wind_on']]].copy()
senspv = senspv.loc[idx[:, :, :, :], (senspv != 0).any(axis=0)].dropna(axis=1, how='all')
senspv.columns = senspv.columns.droplevel(0)
senspv.index = pd.MultiIndex.from_tuples(senspv.index.droplevel([0, 2]))
senspv = senspv.unstack(0)
senspv.index = np.round(senspv.index / ANNUITY_FACTOR / 1000, decimals=2)
senspv = senspv.rename(mapper={'add_r_pv': 'Solar PV', 'add_r_wind_on': 'Wind Onshore',
                               0: r'0 €/t CO$_2$', 25: r'25 €/t CO$_2$', 50: r'50 €/t CO$_2$',
                               75: r'75 €/t CO$_2$', 100: r'100 €/t CO$_2$'}, axis=1)
# senspv = senspv.loc[:, (senspv != 0).any(axis=0)].dropna(axis=1, how='all')

# senspv_nrg = senspv.copy() / 1000
# senspv_nrg.loc[:, idx['Solar PV', :]] = senspv.loc[:, idx['Solar PV', :]] * FLH_PV / 1000
# senspv_nrg.loc[:, idx['Wind Onshore', :]] = senspv.loc[:, idx['Wind Onshore', :]] * FLH_WIND / 1000

var = ['Solar PV', 'Wind Onshore']
price_co2 = ['0 €/t CO$_2$', '25 €/t CO$_2$', '50 €/t CO$_2$', '75 €/t CO$_2$', '100 €/t CO$_2$']  # '0 €/t CO$_2$',

# plot in terms of power
for v in var:
    # mix = pd.MultiIndex.from_product([[v], price_co2])
    # dfp = senspv[senspv.columns.intersection(mix)]
    dfp = senspv.loc[:, idx[v, :]]
    dfp.columns = dfp.columns.droplevel(0)
    plot_lines(dfp, FIGPATH / f'S_PVCost_P_{v}.pdf'.replace(' ', ''),
               xlabel='Capital Cost of PV [€/kWp]', xlim=[650, 250], ylim=[0, 16],
               ylabel='Added Capacity of Wind Turbines [GW]', color=REFUEL_COLORS)

# %% Appendix-Figure that shows change in generation (by fuel) related to switch from wind to pv
reg = 'AT'  # only works for Austria, because of initial RES capacities!
nreg = 'DE'

for pco2 in range(0, 101, 25):
    gbf = pd.DataFrame(columns=['Natural Gas', 'Oil', 'Coal', 'Biomass & Waste', 'Hydro power', 'Solar PV', 'Wind',
                                'Net Exports'])

    # Natural Gas
    ngas = results.loc[idx['base', :, :, :], results.columns.get_level_values(1).str.contains('ng_')]
    ngas = ngas.loc[:, ngas.columns.get_level_values(1).str.contains('AnnGByTec_')]
    ngas = ngas.loc[:, ngas.columns.get_level_values(1).str.contains('el')]
    gbf['Natural Gas'] = ngas.loc[:, reg].sum(axis=1)
    # Oil
    oil = results.loc[idx['base', :, :, :], results.columns.get_level_values(1).str.contains('oil_')]
    oil = oil.loc[:, oil.columns.get_level_values(1).str.contains('AnnGByTec_')]
    oil = oil.loc[:, oil.columns.get_level_values(1).str.contains('el')]
    gbf['Oil'] = oil.loc[:, reg].sum(axis=1)
    # Coal
    coal = results.loc[idx['base', :, :, :], results.columns.get_level_values(1).str.contains('coal_')]
    coal = coal.loc[:, coal.columns.get_level_values(1).str.contains('AnnGByTec_')]
    coal = coal.loc[:, coal.columns.get_level_values(1).str.contains('el')]
    gbf['Coal'] = 0  # coal.loc[:, reg].sum(axis=1)
    # Biomass & Waste
    gbf['Biomass & Waste'] = results.loc[idx['base', :, :, :], idx[reg, 'AnnGBiomass']]
    # Solar PV
    gbf['Solar PV'] = (results.loc[idx['base', :, :, :], idx[reg, 'add_r_pv']] + 1.096) * 1000.7013  # DE: 73
    # Wind Power
    gbf['Wind'] = (results.loc[idx['base', :, :, :], idx[reg, 'add_r_wind_on']] + 2.649) * 1981.5335  # DE: 90.8
    # Run-of-river
    gbf['Hydro power'] = results.loc[idx['base', :, :, :], idx[reg, 'AnnR']].values - gbf['Solar PV'].values \
                         - gbf['Wind'].values
    # Storage
    gbf['Storage'] = results.loc[
        idx['base', :, :, :], idx[reg, 'AnnSIn']]  # AnnSIn because inflows are already included
    gbf['Net Exports'] = results.loc[idx['base', :, :, :], idx[reg, 'AnnX']]

    gbf2plot = gbf.copy()
    gbf2plot.index = gbf.index.droplevel([0, 3])
    gbf2plot = gbf2plot.loc[idx[pco2, :], :]
    gbf2plot = gbf2plot.reindex(gbf2plot.index.levels[1][::-1], level=1, axis=0)
    gbf2plot.index = gbf2plot.index.droplevel(0)
    gbf2plot.index = gbf2plot.index + 1
    gbf2plot = gbf2plot.diff() / 1000

    gbf_plus = gbf2plot.dropna(axis=0).copy()
    gbf_plus[gbf_plus < 0] = 0
    gbf_minus = gbf2plot.dropna(axis=0).copy()
    gbf_minus[gbf_minus > 0] = 0

    # plot figure

    # plotting
    px_height = 375
    px_width = 960
    margin_topbottom = 0.25
    margin_leftright = 0.1
    dpi = 200
    fig_height = px_height / dpi / (1 - 2 * margin_topbottom)
    fig_width = px_width / dpi / (1 - 2 * margin_leftright)

    labs = ['Biomass', 'Coal', 'Run-of-river', 'PV', 'Wind', 'Natural Gas', 'Oil', 'Storage Discharge',
            'Storage Charge',
            'Exports', 'Imports']
    ##cols = ['#757e2e', '#323c47', '#136663', '#ffde65', '#9bdade', '#987019', '#796953', '#af8f19', '#91cec7', '#f8494b', '#a51f22']
    cols = ['#92ad51', '#323c47', '#0f4241', '#ffde65', '#9bdade', '#d29918', '#796953', '#1e8e88', '#91cec7',
            '#f8494b',
            '#B12819']

    colors = ['#d29918', '#796953', '#92ad51', '#91cec7', '#f8494b', '#B12819']

    #          ['Natural Gas', 'Oil', 'Coal', 'Biomass & Waste', 'Hydro power', 'Solar PV', 'Wind']
    # colors = ['#d29918', '#ba9f7f', '#20262d', '#757e2e', '#1e8e88', '#ffde65', '#9bdade', '#c42528']  # all fuels
    # colors = ['#d29918', '#ba9f7f', '#757e2e', '#c42528']

    cumval = 0
    cumval_minus = 0
    fig, ax = plt.subplots(1, 1, figsize=(fig_width, fig_height))
    i = 0
    for col in ['Natural Gas', 'Oil', 'Biomass & Waste', 'Storage', 'Net Exports']:
        ax.bar(gbf_plus.index, gbf_plus[col], bottom=cumval, label=col, color=colors[i])
        ax.bar(gbf_minus.index, gbf_minus[col], bottom=cumval_minus, color=colors[i])
        cumval = cumval + gbf_plus[col]
        cumval_minus = cumval_minus + gbf_minus[col]
        i = i + 1
    ax.set_xlim([14, 0])
    ax.set_ylim([-3, 1])
    # plt.title(f'Carbon price: €{pco2} t$^{{-1}}$ CO$_2$')
    ax.set_ylabel('Change in Electricity Generation [TWh]')
    ax.set_xlabel('Added Capacity of Wind Turbines [GW]')
    plt.legend()
    plt.grid()
    ax.set_axisbelow(True)
    plt.tight_layout()
    # plt.show()
    plt.savefig(APATH / 'doc' / 'figures' / f'gen_by_fuel_{pco2}.pdf', dpi=dpi)
    plt.close()

# %%
"""
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
"""

# %% analysis of sensitivity to transmission constraint
"""
results.loc[:, idx['AT', 'XUnitValue']] = results.loc[:, idx['AT', 'AnnValueX']] / results.loc[:, idx['AT', 'AnnX']]
results.loc[:, idx['DE', 'XUnitValue']] = results.loc[:, idx['DE', 'AnnValueX']] / results.loc[:, idx['DE', 'AnnX']]


sensx = results.loc[idx[['base', 'no_bottleneck'], :, :, 36424], idx[:, ['AnnCO2Emissions', 'AnnR', 'CostCO2',
                                                                         'CostFuel', 'CostOMG', 'CostOMR',
                                                                         'cost_airpol', 'cost_invest_g',
                                                                         'cost_invest_r', 'cost_invest_sv',
                                                                         'cost_zonal_net', 'AnnValueXNet', 'AnnX',
                                                                         'XUnitValue']]]
sensx = sensx.unstack(0)

(sensx.loc[:, idx['AT', 'cost_zonal_net', 'no_bottleneck']] / sensx.loc[:, idx['AT', 'cost_zonal_net', 'base']]-1)*100
"""
