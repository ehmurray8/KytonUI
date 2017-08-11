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
    fig = plt.figure(0)
    ax1 = fig.add_subplot(1, 1, 1)
    
    plt.xlabel('Time (hr)')
    plt.ylabel('Wavelength (nm)')
    fig.suptitle('Baking: Average {} (pm) vs. Time (hr) from start'.format(u'\u0394\u03BB'))

    if animate:
        ani = animation.FuncAnimation(fig, __animate_mvt_graph, interval=1000, fargs=(f_name, ax1,))
        fig.show()
    else:
        __animate_mvt_graph(0, f_name, ax1)
        plt.show()


def __animate_mvt_graph(i, f_name, axis):
    times, wavelen_diffs = __get_mean_wave_diff_v_time_data(f_name)
    axis.clear()
    plt.xlabel('Time (hr)')
    plt.ylabel('Wavelength (pm)')
    axis.plot(times, wavelen_diffs)


def __get_mean_wave_diff_v_time_data(f_name):
    mdata, entries_df = file_helper.parse_csv_file(f_name)
    data_coll = file_helper.create_data_coll(mdata, entries_df)
    times = [(time - mdata.start_time) / 3600 for time in data_coll.times]
    return times, data_coll.mean_wavelen_diffs


def create_wave_power_graph(f_name, animate):
    fig = plt.figure(1)
    ax1 = fig.add_subplot(1, 1, 1)
    fig.suptitle('Baking: Power (dBm) vs. Wavelength (nm)')

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

    #print(str(data_coll))
    
    return data_coll.wavelens, data_coll.powers, mdata.serial_nums


def create_temp_time_graph(f_name, animate):
    fig = plt.figure(2)
    ax1 = fig.add_subplot(1, 1, 1)
    fig.subtitle('Baking: {} Temperature (K) vs. Time (hr) from start.'.format(u'\u0394'))

    if animate:
        ani = animation.FuncAnimation(fig, __animate_temp_graph, interval=1000, fargs=(f_name, ax1,))
        fig.show()
    else:
        __animate_temp_graph(0, f_name, ax1)
        plt.show()


def __animate_temp_graph(i, f_name, axis):
    times, temps = __get_temp_time_graph(f_name)
    axis.clear()
    plt.xlablel('Time (hr)')
    plt.ylablel('Temperature (K)') 

    idx = 0
    axes = []
    #for waves, powers, color in zip(
    
if __name__ == "__main__":
    #create_mean_wave_time_graph("kyton_out.csv", False)
    create_wave_power_graph("kyton_out.csv", False)
