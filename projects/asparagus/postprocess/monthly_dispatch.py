# %% imports
from datetime import datetime

import matplotlib.dates as mdates
import matplotlib.pyplot as plt
import pandas as pd

from src.tools.data_processing import medea_path

APATH = medea_path('projects', 'asparagus')
RPATH = APATH / 'results'
FIGPATH = APATH / 'doc' / 'figures'
REFUEL_COLORS = ['#c72321', '#0d8085', '#f0c220', '#595959', '#3b68f9', '#7794dd']
ANNUITY_FACTOR = 0.05827816
FLH_PV = 1003.36
FLH_WIND = 1983.16
idx = pd.IndexSlice

# %% read data
res = pd.read_csv(RPATH / 'hourly_res.csv', sep=';', decimal=',', index_col=[0, 1, 2, 3, 4], header=[0, 1])
thm = pd.read_csv(RPATH / 'hourly_thermal.csv', sep=';', decimal=',', index_col=[0, 1, 2, 3, 4], header=[0, 1, 2, 3])
s_in = pd.read_csv(RPATH / 'hourly_sin.csv', sep=';', decimal=',', index_col=[0, 1, 2, 3, 4], header=[0, 1])
s_out = pd.read_csv(RPATH / 'hourly_sout.csv', sep=';', decimal=',', index_col=[0, 1, 2, 3, 4], header=[0, 1])
nxp = pd.read_csv(RPATH / 'hourly_export.csv', sep=';', decimal=',', index_col=[0, 1, 2, 3, 4], header=[0, 1])


def to_timeindex(df, startdate, enddate, freq, timeset, firstindex, missing_elements=False):
    """
    Converts a string-number time-index (typically from GAMS output) to a DateTimeIndex compatible with pandas.
    If missing is True, the conversion can handle missing time elements. However, this comes at the cost of drastically
    reduced speed. You might want to consider solving the issue in GAMS.
    :param df: pd.MultiIndex DataFrame with one level indicating time steps
    :param startdate: string or datetime indicating first date of DateTimeIndex to create
    :param enddate: string or datetime indicating last date of DateTimeIndex to create
    :param freq: string indicating frequency of DateTimeIndex to create (typically 'H' hourly)
    :param timeset: string with name of timeset used in GAMS, e.g. 't'
    :param firstindex: int indicating first time-element in GAMS index, e.g. 0 or 1 (if 't0' or 't1')
    :param missing_elements: bool indicating whether time elements are missing
    :return: DateTime-Indexed pd.DataFrame
    """
    tix = pd.date_range(start=startdate, end=enddate, freq=freq, closed='left')
    dfx = df.reset_index().copy()
    dfx.drop(df.columns, axis=1, inplace=True)
    dfx.columns = dfx.columns.get_level_values(0)
    if missing_elements:
        dictix = {f'{str(timeset)}{i}': tix[i - firstindex] for i in range(firstindex, len(tix) + firstindex)}
        dfx.replace(dictix, inplace=True)
        dfix = pd.MultiIndex.from_frame(dfx)
    else:
        nix = dfx.loc[:, ~dfx.iloc[0, :].T.str.contains(f'{timeset}{str(firstindex)}', na=False)]
        index_elements = [nix.iloc[:, i].unique() for i in range(0, len(nix.columns))]
        dfix = pd.MultiIndex.from_product(index_elements + [tix])
    df.index = dfix
    return df


# %% calculate monthly sums
rest = to_timeindex(res, datetime(2016, 1, 1), datetime(2017, 1, 1), 'H', 't', 1)
resm = rest.groupby([rest.index.get_level_values(i) for i in [0, 1, 2]] + [pd.Grouper(freq='M', level=-1)]).sum()

thmt = to_timeindex(thm, datetime(2016, 1, 1), datetime(2017, 1, 1), 'H', 't', 1)
thmm = thmt.groupby([thmt.index.get_level_values(i) for i in [0, 1, 2]] + [pd.Grouper(freq='M', level=-1)]).sum()

s_int = to_timeindex(s_in, datetime(2016, 1, 1), datetime(2017, 1, 1), 'H', 't', 1)
s_inm = s_int.groupby([s_int.index.get_level_values(i) for i in [0, 1, 2]] + [pd.Grouper(freq='M', level=-1)]).sum()

s_outt = to_timeindex(s_out, datetime(2016, 1, 1), datetime(2017, 1, 1), 'H', 't', 1)
s_outm = s_outt.groupby([s_outt.index.get_level_values(i) for i in [0, 1, 2]] + [pd.Grouper(freq='M', level=-1)]).sum()

nxpt = to_timeindex(nxp, datetime(2016, 1, 1), datetime(2017, 1, 1), 'H', 't', 1)
nxpm = nxpt.groupby([nxpt.index.get_level_values(i) for i in [0, 1, 2]] + [pd.Grouper(freq='M', level=-1)]).sum()

# %% data preparation
co2p = 25
wlim = 16
reg = 'AT'
scen = 'base'

dispatch = pd.DataFrame(data=0,
                        columns=['Biomass', 'Coal', 'Ror', 'PV', 'Wind', 'Gas', 'Oil', 'SOut', 'SIn', 'NetX', 'NetI'],
                        index=pd.date_range(start='2016/1/1', end='2017/1/1', freq='M'))
dispatch['Biomass'] = thmm.loc[idx[scen, co2p, wlim, :], idx[reg, :, 'el', 'Biomass']].sum(axis=1).values
dispatch['Gas'] = thmm.loc[idx[scen, co2p, wlim, :], idx[reg, :, 'el', 'Gas']].sum(axis=1).values
dispatch['Coal'] = thmm.loc[idx[scen, co2p, wlim, :], idx[reg, :, 'el', 'Coal']].sum(axis=1).values
dispatch['Oil'] = thmm.loc[idx[scen, co2p, wlim, :], idx[reg, :, 'el', 'Oil']].sum(axis=1).values
dispatch['PV'] = resm.loc[idx[scen, co2p, wlim, :], idx[reg, 'pv']].values
dispatch['Wind'] = resm.loc[idx[scen, co2p, wlim, :], idx[reg, 'wind_on']].values
dispatch['Ror'] = resm.loc[idx[scen, co2p, wlim, :], idx[reg, 'ror']].values
dispatch['SOut'] = s_outm.loc[idx[scen, co2p, wlim, :], idx[reg, :]].sum(axis=1).values
dispatch['SIn'] = -s_inm.loc[idx[scen, co2p, wlim, :], idx[reg, :]].sum(axis=1).values
dispatch['NetX'] = -nxpm.loc[idx[scen, co2p, wlim, :], idx[reg, :]].values
dispatch['NetI'] = -nxpm.loc[idx[scen, co2p, wlim, :], idx[reg, :]].values
dispatch.loc[dispatch['NetX'] > 0, 'NetX'] = 0
dispatch.loc[dispatch['NetI'] < 0, 'NetI'] = 0

dispatch_pos = dispatch[dispatch > 0].copy()
dispatch_pos.fillna(0, inplace=True)

dispatch_neg = dispatch[dispatch < 0].copy()
dispatch_neg.fillna(0, inplace=True)

# data for second subplot
wlimb = 0

dispatchb = pd.DataFrame(data=0,
                         columns=['Biomass', 'Coal', 'Ror', 'PV', 'Wind', 'Gas', 'Oil', 'SOut', 'SIn', 'NetX', 'NetI'],
                         index=pd.date_range(start='2016/1/1', end='2017/1/1', freq='M'))
dispatchb['Biomass'] = thmm.loc[idx[scen, co2p, wlimb, :], idx[reg, :, 'el', 'Biomass']].sum(axis=1).values
dispatchb['Gas'] = thmm.loc[idx[scen, co2p, wlimb, :], idx[reg, :, 'el', 'Gas']].sum(axis=1).values
dispatchb['Coal'] = thmm.loc[idx[scen, co2p, wlimb, :], idx[reg, :, 'el', 'Coal']].sum(axis=1).values
dispatchb['Oil'] = thmm.loc[idx[scen, co2p, wlimb, :], idx[reg, :, 'el', 'Oil']].sum(axis=1).values
dispatchb['PV'] = resm.loc[idx[scen, co2p, wlimb, :], idx[reg, 'pv']].values
dispatchb['Wind'] = resm.loc[idx[scen, co2p, wlimb, :], idx[reg, 'wind_on']].values
dispatchb['Ror'] = resm.loc[idx[scen, co2p, wlimb, :], idx[reg, 'ror']].values
dispatchb['SOut'] = s_outm.loc[idx[scen, co2p, wlimb, :], idx[reg, :]].sum(axis=1).values
dispatchb['SIn'] = -s_inm.loc[idx[scen, co2p, wlimb, :], idx[reg, :]].sum(axis=1).values
dispatchb['NetX'] = -nxpm.loc[idx[scen, co2p, wlimb, :], idx[reg, :]].values
dispatchb['NetI'] = -nxpm.loc[idx[scen, co2p, wlimb, :], idx[reg, :]].values
dispatchb.loc[dispatchb['NetX'] > 0, 'NetX'] = 0
dispatchb.loc[dispatchb['NetI'] < 0, 'NetI'] = 0

dispatchb_pos = dispatchb[dispatchb > 0].copy()
dispatchb_pos.fillna(0, inplace=True)

dispatchb_neg = dispatchb[dispatchb < 0].copy()
dispatchb_neg.fillna(0, inplace=True)

# %% plotting

labs = ['Biomass', 'Coal', 'Run-of-river', 'PV', 'Wind', 'Natural Gas', 'Oil', 'Storage Discharge', 'Storage Charge',
        'Exports', 'Imports']
##cols = ['#757e2e', '#323c47', '#136663', '#ffde65', '#9bdade', '#987019', '#796953', '#af8f19', '#91cec7', '#f8494b', '#a51f22']
cols = ['#92ad51', '#323c47', '#0f4241', '#ffde65', '#9bdade', '#d29918', '#796953', '#1e8e88', '#91cec7', '#f8494b',
        '#B12819']
# cols = ['forestgreen', 'black', 'navy', 'gold', 'deepskyblue', 'yellow',  'teal', 'royalblue', 'lightsteelblue', 'plum', 'fuchsia']

px_height = 480
px_width = 1120
margin_topbottom = 0.25
margin_leftright = 0.1
dpi = 200
fig_height = px_height / dpi / (1 - 2 * margin_topbottom)
fig_width = px_width / dpi / (1 - 2 * margin_leftright)

props = dict(boxstyle='round', facecolor='white', alpha=0.5)

# figure
fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(fig_width, fig_height))
fig.subplots_adjust(left=margin_leftright, right=1 - margin_leftright / 2, top=1 - 0.03, bottom=margin_topbottom,
                    wspace=0.15)
ax1.grid()
ax1.set_axisbelow(True)
ax1.stackplot(dispatch_pos.index, dispatch_pos.T / 1000, colors=cols)
ax1.stackplot(dispatch_neg.index, dispatch_neg.T / 1000, colors=cols)
# ax1.set_ylim([-4, 10])
ax1.set_ylabel('[TWh]')
ax1.xaxis.set_major_formatter(mdates.DateFormatter('%b'))
ax1.text(0.025, 0.975, '(a)', transform=ax1.transAxes, fontsize=14, verticalalignment='top')  # , bbox=props)
ax2.stackplot(dispatchb_pos.index, dispatchb_pos.T / 1000, colors=cols)
ax2.stackplot(dispatchb_neg.index, dispatchb_neg.T / 1000, colors=cols, labels=labs)
# ax2.set_ylim([-4, 10])
ax2.tick_params(labelleft=False)
ax2.xaxis.set_major_formatter(mdates.DateFormatter('%b'))
ax2.text(0.025, 0.975, '(b)', transform=ax2.transAxes, fontsize=14, verticalalignment='top')  # , bbox=props)
handles, labels = ax2.get_legend_handles_labels()
plt.legend(handles, labels, loc='lower center', bbox_to_anchor=(-0.125, -0.33), ncol=4)
plt.grid()
ax2.set_axisbelow(True)
plt.savefig(APATH / 'doc' / 'figures' / f'dispatch_{reg}.pdf', dpi=dpi)
plt.close(fig)
