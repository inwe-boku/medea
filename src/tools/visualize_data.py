# %% imports
import itertools

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd


# %% plotting functions
def plot_subn(df, path, width=2, xlim=None, ylim=None, xlabel=None, ylabel=None, color=None):
    """
    plots each column of a pandas DataFrame on a separate subplot. Uses column names as subplot-titles.
    :param df: pandas DataFrame to be plotted
    :param path: str of output path and file name
    :param width: number of subplots arranged horizontally
    :param xlim: list of upper and lower limit of x-axis
    :param ylim: list of upper and lower limit of y-axis
    :param xlabel: x-axis label
    :param ylabel: y-axis label
    :param color: color palette or list of colors
    :return: file with plot
    """
    if isinstance(df, pd.DataFrame):
        ncols = len(df.columns)
    else:
        raise TypeError

    sub_length = np.ceil(ncols / width).astype(int)
    sub_boxes = list(itertools.product(range(0, width), range(0, sub_length)))

    figure, axis = plt.subplots(width, sub_length, figsize=(8, 5))
    for col in range(0, ncols):
        a = sub_boxes[col][0]
        b = sub_boxes[col][1]

        if color is not None:
            axis[a, b].plot(df.iloc[:, col], linewidth=2, color=color[col])
        else:
            axis[a, b].plot(df.iloc[:, col], linewidth=2)

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
    plt.savefig(path)
    plt.close()


def plot_lines(df, path, xlim=None, ylim=None, xlabel=None, ylabel=None, color=None):
    """
    line plot of each column in pandas DataFrame.
    :param df: a pandas DataFrame
    :param path: str of output file and folder
    :param xlim: list of upper and lower x-axis limit
    :param ylim: list of upper and lower y-axis limit
    :param xlabel: str of x-axis label
    :param ylabel: str of y-axis label
    :param color: color palette or list of colors
    :return: file with plot
    """
    if isinstance(df, pd.DataFrame):
        ncols = len(df.columns)
    elif isinstance(df, pd.Series):
        ncols = 1
    else:
        raise TypeError

    figure, axis = plt.subplots(1, 1, figsize=(8, 5))
    axis.set_ylabel(ylabel)
    axis.set_xlabel(xlabel)

    if isinstance(df, pd.DataFrame):
        for col in range(0, ncols):
            axis.plot(df.iloc[:, col], linewidth=2, color=color[col])
    elif isinstance(df, pd.Series):
        axis.plot(df, color=color[0])
    else:
        raise TypeError

    if isinstance(df, pd.DataFrame):
        axis.legend(df.columns)
    elif isinstance(df, pd.Series):
        axis.legend([df.name])
    else:
        raise TypeError

    axis.set_ylim(ylim)
    axis.set_xlim(xlim)
    axis.grid()
    plt.tight_layout()
    plt.savefig(path)
    plt.close()


def plot_sublines(df, path, width=2, midx_level=0, subtitle=True, xlim=None, ylim=None, xlabel=None, ylabel=None,
                  color=None):
    """
    plots multiindex pd.DataFrame to multiple line-subplots
    :param df: Pandas MultiIndex DataFrame
    :param path: str with output filename and directory
    :param width: number of subplots in a horizontal row
    :param midx_level: MultiIndex level to group plots by
    :param subtitle: boolean, if True generate title for each subplot; False: generate long legend entries instead
    :param xlim: list of upper and lower x-axis limit
    :param ylim: list of upper and lower y-axis limit
    :param xlabel: x-axis label
    :param ylabel: y-axis label
    :param color: color palette or list of colors
    :return: file with subplots
    """
    # determine length and width of subfigures
    idx_to_group = list(df.columns.get_level_values(midx_level).unique())
    num_subfigures = len(idx_to_group)
    sub_length = np.ceil(num_subfigures / width).astype(int)

    fig = plt.figure(figsize=(8, 5))
    for subplot in range(0, num_subfigures):
        data_to_plot = df.xs(idx_to_group[subplot], axis=1, level=midx_level)
        _, num_lines = data_to_plot.shape
        ax = fig.add_subplot(width, sub_length, subplot + 1)

        if not color:
            ax.plot(data_to_plot, linewidth=2)
        elif len(color) == num_lines:
            for c in range(0, num_lines):
                ax.plot(data_to_plot.iloc[:, c], linewidth=2, color=color[c])
        else:
            raise TypeError(f'Colors misspecified. Should be {num_lines} colors')

        if subtitle:
            ax.set_title(idx_to_group[subplot])
            ax.legend(data_to_plot.columns)
        if not subtitle:
            legend_entries = [", ".join(i) for i in itertools.product(list(data_to_plot.columns),
                                                                      [idx_to_group[subplot]])]
            ax.legend(legend_entries)
        ax.set_ylabel(ylabel)
        ax.set_xlabel(xlabel)
        ax.set_ylim(ylim)
        ax.set_xlim(xlim)
        ax.grid()

    plt.tight_layout()
    plt.savefig(path)
    plt.close()
