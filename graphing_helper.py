"""Module to help with graphing."""

import numpy as np
import pandas as pd
import matplotlib.animation as animation
from matplotlib import style
import matplotlib.pyplot as plt
import pprint
import file_helper

style.use("ggplot")

def create_mean_wave_time_graph(f_name, animate):
    """Create a mpl graph in a separate window."""
    fig = plt.figure(0, figsize=(8,6))
    ax1 = fig.add_subplot(1, 1, 1)

    plt.xlabel('Time (hr)')
    plt.ylabel('Wavelength (pm)'.format(u'\u0394'))
    fig.suptitle('Average {} (pm) vs. Time (hr) from start'.format(u'\u0394\u03BB'))

    if animate:
        ani = animation.FuncAnimation(fig, __animate_mwt_graph, interval=1000, fargs=(f_name, ax1,))
        fig.show()
    else:
        __animate_mwt_graph(0, f_name, ax1)
        plt.show()


def __animate_mwt_graph(i, f_name, axis):
    times, wavelen_diffs = __get_mean_wave_diff_v_time_data(f_name)
    axis.clear()
    plt.xlabel('Time (hr)')
    plt.ylabel('Average {} Wavelength (pm)'.format(u'\u0394'))
    axis.plot(times, wavelen_diffs)


def __get_mean_wave_diff_v_time_data(f_name):
    mdata, entries_df = file_helper.parse_csv_file(f_name)
    data_coll = file_helper.create_data_coll(mdata, entries_df)
    times = [(time - mdata.start_time) / 3600 for time in data_coll.times]
    return times, data_coll.mean_wavelen_diffs


def create_wave_power_graph(f_name, animate):
    fig = plt.figure(1, figsize=(8,6))
    ax1 = fig.add_subplot(1, 1, 1)
    fig.suptitle('Power (dBm) vs. Wavelength (nm)')

    if animate:
        ani = animation.FuncAnimation(fig, __animate_wp_graph, interval=1000, fargs=(f_name, ax1,))
        fig.show()
    else:
        __animate_wp_graph(0, f_name, ax1)
        plt.show()


def __animate_wp_graph(i, f_name, axis):
    wavelens, powers, snums = __get_wave_power_graph(f_name)
    axis.clear()
    plt.xlabel('Wavelength (nm)')
    plt.ylabel('Power (dBm)')

    idx = 0
    axes = []
    for waves, powers, color in zip(wavelens, powers, file_helper.HEX_COLORS):
        axes.append(axis.scatter(waves, powers, color=color, s=75))
        idx += 1

    legend = axis.legend(axes, snums, bbox_to_anchor=(1.10, 1.10), loc='upper right', borderaxespad=0.,\
                    ncol=int(len(snums) / 2 + 0.5), fontsize=8)


def __get_wave_power_graph(f_name):
    mdata, entries_df = file_helper.parse_csv_file(f_name)
    data_coll = file_helper.create_data_coll(mdata, entries_df)

    return data_coll.wavelens, data_coll.powers, mdata.serial_nums


def create_temp_time_graph(f_name, animate):
    fig = plt.figure(2, figsize=(8,6))
    ax1 = fig.add_subplot(1, 1, 1)
    fig.suptitle('{} Temperature (K) vs. Time (hr) from start.'.format(u'\u0394'))

    if animate:
        ani = animation.FuncAnimation(fig, __animate_temp_graph, interval=1000, fargs=(f_name, ax1,))
        fig.show()
    else:
        __animate_temp_graph(0, f_name, ax1)
        plt.show()


def __animate_temp_graph(i, f_name, axis):
    times, temps = __get_temp_time_graph(f_name)
    axis.clear()
    plt.xlabel('Time (hr)')
    plt.ylabel('Temperature (K)'.format(u'\u0394')) 
    axis.plot(times, temps)


def __get_temp_time_graph(f_name):
    mdata, entries_df = file_helper.parse_csv_file(f_name)
    data_coll = file_helper.create_data_coll(mdata, entries_df)
    times = [(time - mdata.start_time) / 3600 for time in data_coll.times]
    return times, data_coll.temp_diffs


def create_mean_power_time_graph(f_name, animate):
    """Create a mpl graph in a separate window."""
    fig = plt.figure(3, figsize=(8,6))
    ax1 = fig.add_subplot(1, 1, 1)
    
    plt.xlabel('Time (hr)')
    plt.ylabel('Power (dBm)')
    fig.suptitle('Average Power (dBm) vs. Time (hr) from start')

    if animate:
        ani = animation.FuncAnimation(fig, __animate_mpt_graph, interval=1000, fargs=(f_name, ax1,))
        fig.show()
    else:
        __animate_mpt_graph(0, f_name, ax1)
        plt.show()


def __animate_mpt_graph(i, f_name, axis):
    times, wavelen_diffs = __get_mean_power_diff_v_time_data(f_name)
    axis.clear()
    plt.xlabel('Time (hr)')
    plt.ylabel('Power (dBm)')
    axis.plot(times, wavelen_diffs)


def __get_mean_power_diff_v_time_data(f_name):
    mdata, entries_df = file_helper.parse_csv_file(f_name)
    data_coll = file_helper.create_data_coll(mdata, entries_df)
    times = [(time - mdata.start_time) / 3600 for time in data_coll.times]
    return times, data_coll.mean_power_diffs


def create_indiv_waves(f_name, animate):
    """Create individual wavelengths graph."""
    fig = plt.figure(4, figsize=(8,6))
    ax1 = fig.add_subplot(1, 1, 1)

    plt.xlabel('Time (hr)')
    plt.ylabel('Wavelength (nm)')
    fig.suptitle('Wavelengths (nm) vs. Time (hr)')

    if animate:
        ani = animation.FuncAnimation(fig, __animate_indiv_waves, interval=1000, fargs=(f_name, ax1,))
        fig.show()
    else:
        __animate_indiv_waves(0, f_name, ax1)
        plt.show()


def __animate_indiv_waves(f_name):
    times, wavelens, snums = __get_indiv_waves_data(f_name)
    axis.clear()
    plt.xlabel('Time (hr)')
    plt.ylabel('Wavelength (nm)')

    idx = 0
    axes = []
    for waves, powers, color in zip(wavelens, powers, file_helper.HEX_COLORS):
        axes.append(axis.scatter(waves, powers, color=color, s=75))
        idx += 1

    legend = axis.legend(axes, snums, bbox_to_anchor=(1.10, 1.10), loc='upper right', borderaxespad=0.,\
                    ncol=int(len(snums) / 2 + 0.5), fontsize=8)


def __get_indiv_waves_diffs_data(f_name):
    mdata, entries_df = file_helper.parse_csv_file(f_name)
    data_coll = file_helper.create_data_coll(mdata, entries_df)
    times = [(time - mdata.start_time) / 3600 for time in data_coll.times]
    return times, data_coll.wavelen_diffs


if __name__ == "__main__":
    #create_mean_wave_time_graph("kyton_out.csv", False)
    #create_wave_power_graph("kyton_out.csv", False)
    #create_temp_time_graph("kyton_out.csv", False)
    create_mean_power_time_graph("kyton_out.csv", False)
