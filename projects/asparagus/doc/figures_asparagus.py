from pathlib import Path

import matplotlib.pylab as pylab
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

import config as cfg
from src.tools.data_processing import medea_path
from src.tools.visualize_data import plot_lines, plot_subn

params = {
    'legend.fontsize': 9,
    'axes.labelsize': 9,
    'axes.titlesize': 10,
    'xtick.labelsize': 9,
    'ytick.labelsize': 9}
pylab.rcParams.update(params)

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
results.loc[:, idx['AT', 'AnnX']] = results.loc[:, idx['DE', 'AnnX']]

itm = pd.read_csv(Path(cfg.MEDEA_ROOT_DIR) / 'data' / 'processed' / 'medea_regional_timeseries.csv', index_col=[0])
itm.index = pd.to_datetime(itm.index)

# %% horizontal bar plot of cost in unconstrained baseline
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

# %% bar plot of cost components
pco2 = 25
region = 'AT'
scenario = 'base'

costcomps = ['cost_invest_g', 'cost_invest_r', 'cost_invest_sv', 'CostCO2', 'CostFuel', 'CostOMG',
             'CostOMR', 'AnnValueI', 'AnnValueX']

coco = results.loc[idx[scenario, :, :, :], idx[region, costcomps]]
coco.index = coco.index.droplevel([0, 3])
coco.columns = coco.columns.droplevel(0)

coco['Invest'] = coco.loc[:, ['cost_invest_r', 'cost_invest_g', 'cost_invest_sv']].sum(axis=1)
coco['O&M'] = coco.loc[:, ['CostOMR', 'CostOMG']].sum(axis=1)
coco['Fuel & CO$_2$'] = coco.loc[:, ['CostCO2', 'CostFuel']].sum(axis=1)
coco['Trade Balance'] = - coco.loc[:, ['AnnValueX', 'AnnValueI']].sum(axis=1)
coco = coco.reindex(coco.index.levels[1][::-1], level=1, axis=0)

ploco = coco.loc[idx[pco2, :], ['Invest', 'O&M', 'Fuel & CO$_2$', 'Trade Balance']] / 1000
ploco.index = ploco.index.droplevel(0)
ploco = ploco.diff()

ploco_plus = ploco.dropna(axis=0).copy()
ploco_plus[ploco_plus < 0] = 0
ploco_minus = ploco.dropna(axis=0).copy()
ploco_minus[ploco_minus > 0] = 0

# %% plot cost comparison figure
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
ax.set_xlim([11, -1])
ax.set_ylabel('Change in Net System Cost [Mio EUR]')
ax.set_xlabel('Added Capacity of Wind Turbines [GW]')
plt.legend()
plt.grid()
ax.set_axisbelow(True)
plt.tight_layout()
# plt.show()
plt.savefig(APATH / 'doc' / 'figures' / 'cost_components.pdf', dpi=dpi)
plt.close()

# %% figure showing renewable generation to illustrate when policy is binding
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

# %% figure of seasonal variation in ror, wind_on, pv, cons_el
# transform data
cols = ['AT-wind_on-generation', 'AT-ror-generation', 'AT-pv-generation', 'AT-power-load']
seasm = itm.loc['2016', cols].resample('M', label='left').mean() / itm.loc['2016', cols].mean()
seasm = seasm.rename(mapper={'AT-pv-generation': 'Solar PV', 'AT-wind_on-generation': 'Wind onshore',
                             'AT-ror-generation': 'Run-of-river', 'AT-power-load': 'Electricity consumption'}, axis=1)
# plot figure
plot_lines(seasm, FIGPATH / 'seasonal.pdf', ylabel='normalized generation / consumption',
           x_ax_date_format='%b', color=REFUEL_COLORS)

# %% figure showing electricity generation, net exports, fossil generation, co2 emissions in baseline for all wind caps
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

# %% figure showing the opportunity cost of wind power in baseline
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
pv_cost = 36424

oc_costdiff = ocw.loc[idx[scenario, co2_price, :, pv_cost], 'oc_wind'].unstack(1)
oc_costdiff = oc_costdiff.unstack(0)
oc_costdiff.index = oc_costdiff.index.get_level_values(0)

# plot figures
for sc in scenario:
    oc_cd = oc_costdiff.loc[:, idx[:, sc]].copy()
    oc_cd.columns = oc_cd.columns.get_level_values(0)
    oc_cd = oc_cd.add_prefix('CO$_2$ price: ').add_suffix(' €/t')

    plot_lines(oc_cd / 1000, FIGPATH / f'oc_{sc}.pdf',
               xlabel='Added Capacity of Wind Turbines [GW]', xlim=[14, 0],
               ylabel='\'000 € / MW', ylim=[0, 50], color=REFUEL_COLORS)

# %% figure showing the optimal deployment of wind power conditional on cost of pv
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
price_co2 = ['0 €/t CO$_2$', '25 €/t CO$_2$', '50 €/t CO$_2$', '75 €/t CO$_2$', '100 €/t CO$_2$']  # '0 €/t CO$_2$',

# plot in terms of power
for v in var:
    mix = pd.MultiIndex.from_product([[v], price_co2])
    dfp = senspv.loc[:, idx[mix]]
    dfp.columns = dfp.columns.droplevel(0)
    plot_lines(dfp, FIGPATH / f'S_PVCost_P_{v}.pdf',
               xlabel='Capital Cost of PV [€/kWp]', xlim=[650, 250],
               ylabel='Added Capacity of Wind Turbines [GW]', color=REFUEL_COLORS)

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

# %% figure showing the opportunity cost of wind power in low cost scenario
