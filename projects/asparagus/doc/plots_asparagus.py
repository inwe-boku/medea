import itertools
import os

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

import config as cfg


# %% define plotting functions
def plot_subn(df, fname, width=2, xlim=None, ylim=None, xlabel=None, ylabel=None, color=None):
    """
    plots each column of a pandas dataframe on a seperate subplot. Uses column names as subplot-titles.
    :param df:
    :param fname:
    :param width:
    :param xlim:
    :param ylim:
    :param xlabel:
    :param ylabel:
    :param color:
    :return:
    """
    ncols = len(df.columns)
    sub_length = np.ceil(ncols / width).astype(int)
    sub_boxes = list(itertools.product(range(0, width), range(0, sub_length)))

    figure, axis = plt.subplots(width, sub_length, figsize=(8, 5))
    for col in range(0, ncols):
        a = sub_boxes[col][0]
        b = sub_boxes[col][1]

        if color is not None:
            axis[a, b].plot(df.iloc[:, col], color=color[col])
        else:
            axis[a, b].plot(df.iloc[:, col])

        if xlabel is not None:
            axis[a, b].set_xlabel(xlabel)

        if (ylabel is not None) & (len(ylabel) == 1):
            axis[a, b].set_ylabel(*ylabel)
        elif (ylabel is not None) & (len(ylabel) == ncols):
            axis[a, b].set_ylabel(ylabel[col])

        if xlim is not None:
            axis[a, b].set_xlim(xlim[0], xlim[1])

        if ylim is not None:
            axis[a, b].set_ylim(ylim[0], ylim[1])

        axis[a, b].grid()
        axis[a, b].set_title(df.columns[col])
    plt.tight_layout()
    plt.savefig(fname)
    plt.close()


def plot_lines(df, fname, xlim=None, ylim=None, xlabel=None, ylabel=None, color=None):
    """
    line plot of each column in df.
    :param df:
    :param fname:
    :param xlim:
    :param ylim:
    :param xlabel:
    :param ylabel:
    :param color:
    :return:
    """
    ncols = len(df.columns)

    figure, axis = plt.subplots(1, 1, figsize=(8, 5))
    axis.set_ylabel(ylabel)
    axis.set_xlabel(xlabel)
    for col in range(0, ncols):
        axis.plot(df.iloc[:, col], color=color[col])
    axis.set_ylim(ylim)
    axis.set_xlim(xlim)
    axis.grid()
    axis.legend(df.columns)
    plt.tight_layout()
    plt.savefig(fname)
    plt.close()


# %% ----- ----- ----- ----- settings ----- ----- ----- -----
idx = pd.IndexSlice
PRICE_CO2 = 90
REFUEL_COLORS = ['#c72321', '#0d8085', '#f0c220', '#595959']
RES_COLORS = ['#d69602', '#ffd53d', '#3758ba', '#7794dd']
RES_COLORS3 = ['#d69602', '#e5b710', '#ffd53d', '#3758ba', '#3b68f9', '#7794dd']

ANNUITY_FACTOR = 0.05827816
FLH_PV = 857.4938
FLH_WINDON = 2015.0359

RPATH = os.path.join(cfg.MEDEA_ROOT_DIR, 'projects', 'asparagus', 'results', 'results.csv')
FPATH = os.path.join(cfg.MEDEA_ROOT_DIR, 'projects', 'asparagus', 'doc', 'figures')

if not os.path.exists(FPATH):
    os.makedirs(FPATH)

# %% ----- ----- ----- ----- read results ----- ----- ----- -----
results = pd.read_csv(RPATH, decimal=',', delimiter=';', index_col=[0, 1, 2, 3, 4], header=[0])
results = results.unstack(-1)

# %% ----- ----- ----- plot wind restriction: changes in system operation ----- ----- -----
# net electricity generation, net electricity exports, fossil thermal generation, CO2 emissions from energy generation

# prepare data
restrict_sysops = results.loc[idx['base', PRICE_CO2, :, 36715], idx['AT', ['gen_el', 'gen_biomass', 'gen_storages',
                                                                           'in_storages', 'gen_renew', 'co2emission']]]
restrict_sysops[('AT', 'exports')] = results.loc[idx['base', PRICE_CO2, :, 36715], idx['DE', 'exports']]
restrict_sysops.index = restrict_sysops.index.droplevel([0, 1, 3])
restrict_sysops.columns = restrict_sysops.columns.droplevel(0)
restrict_sysops['Net electricity generation'] = (restrict_sysops[['gen_el', 'gen_storages', 'gen_renew']].sum(axis=1)
                                                 - restrict_sysops['in_storages'])
restrict_sysops['Fossil thermal generation'] = restrict_sysops['gen_el'] - restrict_sysops['gen_biomass']
restrict_sysops = restrict_sysops.drop(['gen_biomass', 'gen_el', 'gen_renew', 'gen_storages', 'in_storages'], axis=1)
restrict_sysops = restrict_sysops.rename(columns={'co2emission': 'CO2 emissions from energy generation',
                                                  'exports': 'Net electricity exports'})
restrict_sysops = restrict_sysops[['Net electricity generation', 'Net electricity exports',
                                   'Fossil thermal generation', 'CO2 emissions from energy generation']]

# plot data
plot_subn(restrict_sysops / 1000, os.path.join(FPATH, 'sysops.pdf'), xlim=[18, 0], color=REFUEL_COLORS,
          xlabel='Added Capacity of Wind [GW]', ylabel=['TWh', 'TWh', 'TWh', 'million t'])

# %% ----- ----- ----- plot wind restriction: changes in cost ----- ----- -----
# system cost, electricity trade balance, system cost net of trade, cost of air pollution (SOx, NOx, PM)
undisturbed_cost = results.loc[idx['base', :, :, 36715], idx['AT', ['syscost', 'export_value', 'import_value',
                                                                    'cost_airpol']]]
undisturbed_cost.index = undisturbed_cost.index.droplevel([0, 3])
undisturbed_cost.columns = undisturbed_cost.columns.droplevel(0)
undisturbed_cost['trade_balance'] = undisturbed_cost[['export_value', 'import_value']].sum(axis=1)
undisturbed_cost['syscost_net'] = undisturbed_cost['syscost'] - undisturbed_cost['trade_balance']
undisturbed_cost = undisturbed_cost.drop(['export_value', 'import_value'], axis=1)
undisturbed_cost = undisturbed_cost.rename(columns={'syscost': 'System Cost',
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

# %% line plot of cost of undisturbed landscapes - baseline capital cost of pv
undisturbed_base = undisturbed_cost[['System cost net of trade',
                                     'Cost of air pollution (SOx, NOx, PM)']].sum(axis=1).unstack(0)
wind_add = results.loc[idx['base', :, :, 36715], idx['AT', 'add_wind_on']].unstack(1)
wind_add.index = wind_add.index.droplevel([0, 2])

undisturbed_marginal = undisturbed_base.iloc[::-1].diff().divide(wind_add.iloc[::-1].diff().round(8), axis=0) * -1
undisturbed_marginal.columns = [f'CO2 Price: {p} €/t' for p in undisturbed_marginal.columns]

plot_lines(undisturbed_marginal / 1000, os.path.join(FPATH, 'undisturbed_base.pdf'), xlim=[18, 0], ylim=[0, 75],
           xlabel='Added Capacity of Wind [GW]', ylabel='thousand € / MW', color=REFUEL_COLORS)

# %% line plot of cost of undisturbed landscapes - low capital cost of pv
undisturbed_cost_low = results.loc[idx['base', :, :, 16715], idx['AT', ['syscost', 'export_value', 'import_value',
                                                                        'cost_airpol']]]
undisturbed_cost_low.index = undisturbed_cost_low.index.droplevel([0, 3])
undisturbed_cost_low.columns = undisturbed_cost_low.columns.droplevel(0)
undisturbed_cost_low['trade_balance'] = undisturbed_cost_low[['export_value', 'import_value']].sum(axis=1)
undisturbed_cost_low['syscost_net'] = undisturbed_cost_low['syscost'] - undisturbed_cost_low['trade_balance']
undisturbed_cost_low['total_cost'] = undisturbed_cost_low[['syscost_net', 'cost_airpol']].sum(axis=1)

wind_add_low = results.loc[idx['base', :, :, 16715], idx['AT', 'add_wind_on']].unstack(1)
wind_add_low.index = wind_add_low.index.droplevel([0, 2])

undisturbed_marginal_low = (undisturbed_cost_low['total_cost'].unstack(0).iloc[::-1].diff().divide(
    wind_add_low.iloc[::-1].diff().round(8), axis=0)) * -1

undisturbed_marginal_low.columns = [f'CO2 Price: {p} €/t' for p in undisturbed_marginal_low.columns]

plot_lines(undisturbed_marginal_low / 1000, os.path.join(FPATH, 'undisturbed_low.pdf'), xlim=[18, 0], ylim=[0, 75],
           xlabel='Added Capacity of Wind [GW]', ylabel='thousand € / MW', color=REFUEL_COLORS)

# %% plot sensitivity of optimal res capacity deployment to capital cost of pv
sensitivity = results.loc[idx['cheappv', :, 18, :], idx['AT', ['add_pv', 'add_wind_on']]].copy()
sensitivity.index = sensitivity.index.droplevel([0, 2])
sensitivity.columns = sensitivity.columns.droplevel(0)
sensitivity = sensitivity.unstack(0)
sensitivity.index = np.round(sensitivity.index / ANNUITY_FACTOR / 1000, decimals=2)
sensitivity = sensitivity.rename(mapper={'add_pv': 'Solar PV', 'add_wind_on': 'Wind Onshore',
                                         30: '30 €/t CO2', 60: '60 €/t CO2', 120: '120 €/t CO2'}, axis=1)
sensitivity_nrg = sensitivity.copy()
sensitivity.columns = sensitivity.columns.map(', '.join)

plot_lines(sensitivity, os.path.join(FPATH, 'sens_cap.pdf'),
           xlim=[650, 250], ylim=None, xlabel='Capital cost of solar PV [€/kWp]', ylabel='GW', color=RES_COLORS3)

# %% plot sensitivity of optimal res generation to capital cost of pv
sensitivity_nrg.loc[:, idx['Solar PV', :]] = sensitivity_nrg.loc[:, idx['Solar PV', :]] * FLH_PV / 1000
sensitivity_nrg.loc[:, idx['Wind Onshore', :]] = sensitivity_nrg.loc[:, idx['Wind Onshore', :]] * FLH_WINDON / 1000
sensitivity_nrg.columns = sensitivity_nrg.columns.map(', '.join)

plot_lines(sensitivity_nrg, os.path.join(FPATH, 'sens_nrg.pdf'),
           xlim=[650, 250], ylim=None, xlabel='Capital cost of solar PV [€/kWp]', ylabel='TWh', color=RES_COLORS3)

# %% plot why wind is not pv
# plot generation profile in one summer week and one winter week
mts = pd.read_csv(os.path.join(cfg.MEDEA_ROOT_DIR, 'data', 'processed', 'medea_regional_timeseries.csv'),
                  parse_dates=True, index_col='DateTime')
mta = mts.loc['2016-01-01':'2016-12-31', ['AT-wind_on-profile', 'AT-pv-profile']]

fig, axs = plt.subplots(2, figsize=(8, 5))
# winter week
axs[0].plot(mta.loc['2016-06-13':'2016-06-19', 'AT-pv-profile'] * 100, color=RES_COLORS[0])
axs[0].plot(mta.loc['2016-06-13':'2016-06-19', 'AT-wind_on-profile'] * 100, color=RES_COLORS[2])
axs[0].set_ylabel('% of installed capacity')
axs[0].set_ylim(0, 100)
axs[0].grid()
axs[0].legend(['Solar PV', 'Wind'], loc='upper left')
axs[0].set_title('Summer Week')
# summer week
axs[1].plot(mta.loc['2016-12-05':'2016-12-11', 'AT-pv-profile'] * 100, color=RES_COLORS[0])
axs[1].plot(mta.loc['2016-12-05':'2016-12-11', 'AT-wind_on-profile'] * 100, color=RES_COLORS[2])
axs[1].set_ylabel('% of installed capacity')
axs[1].set_ylim(0, 100)
axs[1].grid()
axs[1].legend(['Solar PV', 'Wind'], loc='upper left')
axs[1].set_title('Winter week')

plt.tight_layout()
plt.savefig(os.path.join(FPATH, 'wind_not_pv.pdf'))
plt.close()
