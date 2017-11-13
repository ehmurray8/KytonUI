"""Module to help with graphing."""
# pylint: disable=import-error, relative-import, unused-argument

import os
import stat
import platform
from tkinter import messagebox
import matplotlib.animation as animation
from matplotlib import style
import matplotlib.pyplot as plt
import file_helper
style.use("ggplot")

TEST_FILE = "./output/test0930-2.csv"

PAUSE = False

def __file_error(f_name): 
    messagebox.showwarning("File Error", "Inconsistency in the number of reading being stored in file {}." .format(f_name))

def show_main_plots(fig, num, is_cal, fname=TEST_FILE):
    # Need to check to make sure Csv is populated, if it is then get axes from graph_helper
    axes = []
    offs = 1
    need_warning = True

    graph_funcs = [create_indiv_waves_graph, create_wave_power_graph, create_indiv_powers_graph,
                   create_mean_power_time_graph, create_mean_wave_time_graph, create_temp_time_graph]

    for i, func in enumerate(graph_funcs):
        axis = func(fname, False, fig, num+offs, is_cal, need_warning)
        axes.append(axis)
        if axis is None:
            need_warning = False
        offs += 1

    if is_cal:
        axis = create_drift_rates_graph(fname, False, fig, num+offs, need_warning)
        axes.append(axis)
    return axes

def create_mean_wave_time_graph(f_name, animate, fig, dims, is_cal, need_warning):
    """Create a mpl graph in a separate window."""
    if check_valid_file(f_name, is_cal):
        try:
            ax1 = fig.add_subplot(dims)
            if animate:
                _ = animation.FuncAnimation(fig, __animate_mwt_graph,
                        interval=1000, fargs=(f_name, ax1,))
            else:
                __animate_mwt_graph(0, f_name, ax1)
            return ax1
        except IndexError:
            if need_warning:
                __file_error(f_name)


def __animate_mwt_graph(i, f_name, axis):
    times, wavelen_diffs = __get_mean_wave_diff_time_data(f_name)
    axis.clear()
    axis.set_title('Average {} (pm) vs. Time (hr) from start'.format(u'\u0394\u03BB'), fontsize=12)
    axis.set_xlabel('Time (hr)')
    axis.set_ylabel('Wavelength (pm)')
    axis.plot(times, wavelen_diffs)


def __get_mean_wave_diff_time_data(f_name):
    if platform.system() != 'Linux':
        os.chmod(f_name, stat.S_IRWXU)
    mdata, entries_df = file_helper.parse_csv_file(f_name)
    if platform.system() != 'Linux':
        os.chmod(f_name, stat.S_IREAD)
    data_coll = file_helper.create_data_coll(mdata, entries_df)
    times = [(time - mdata.start_time) / 3600 for time in data_coll.times]
    return times, data_coll.mean_wavelen_diffs


def create_wave_power_graph(f_name, animate, fig, dims, is_cal, need_warning):
    """Creates the wavelength vs. power graph."""
    if check_valid_file(f_name, is_cal):
        try:
            ax1 = fig.add_subplot(dims)
            if animate:
                _ = animation.FuncAnimation(fig, __animate_wp_graph,
                        interval=1000, fargs=(f_name, ax1,))
            else:
                __animate_wp_graph(0, f_name, ax1)
            return ax1
        except IndexError:
            if need_warning:
                __file_error(f_name)


def __animate_wp_graph(i, f_name, axis):
    wavelens, powers, snums = __get_wave_power_graph(f_name)
    axis.clear()
    axis.set_title('Power (dBm) vs. Wavelength (nm)', fontsize=12)#, x=.35)
    axis.set_xlabel('Wavelength (nm)')
    axis.set_ylabel('Power (dBm)')

    idx = 0
    axes = []
    for waves, powers, color in zip(wavelens, powers, file_helper.HEX_COLORS):
        axes.append(axis.scatter(waves, powers, color=color, s=75))
        idx += 1

    legend = axis.legend(axes, snums, bbox_to_anchor=(.5, 1.25), loc='upper center', #borderaxespad=0.,
            ncol=int(len(snums) / 2 + 0.5), fontsize=10, fancybox=True, shadow=True)
    for text in legend.get_texts():
        text.set_color("black")


def __get_wave_power_graph(f_name):
    mdata, entries_df = file_helper.parse_csv_file(f_name)
    data_coll = file_helper.create_data_coll(mdata, entries_df)

    return data_coll.wavelens, data_coll.powers, mdata.serial_nums


def create_temp_time_graph(f_name, animate, fig, dims, is_cal, need_warning):
    """Creates the temperature vs. time graph."""
    if check_valid_file(f_name, is_cal):
        try:

            #ax1 = plt.subplot2grid((10, 1), (1, 0), rowspan=5, colspan=1)
            #ax2 = plt.subplot2grid((10, 1), (6, 0), rowspan=4, colspan=1, sharex=ax1)
            ax2=None
            ax1 = fig.add_subplot(dims)

            if animate:
                _ = animation.FuncAnimation(
                    fig, __animate_temp_graph, interval=1000, fargs=(f_name, ax1, ax2, ))
            else:
                __animate_temp_graph(0, f_name, ax1, ax2)
            return ax1
        except IndexError:
            if need_warning:
                __file_error(f_name)


def __animate_temp_graph(i, f_name, ax1, ax2):
    times, temp_diffs, temps = __get_temp_time_graph(f_name)
    ax1.clear()
    #ax2.clear()

    ax1.set_title('Raw Temperature (K) vs. Time (hr) from start.', fontsize=12)
    #ax1 = plt.subplot2grid((10, 1), (0, 0), rowspan=7, colspan=1)
    ax1.set_ylabel('Temperature (K)')
    #ax2 = plt.subplot2grid((10, 1), (7, 0), rowspan=3, colspan=1, sharex=ax1)

    ax1.set_xlabel('Time (hr)')
    #ax2.set_ylabel('{} Temperature (K)'.format(u'\u0394'))
    ax1.plot(times, temps)
    #ax2.plot(times, temp_diffs, color='b')


def __get_temp_time_graph(f_name):
    mdata, entries_df = file_helper.parse_csv_file(f_name)
    data_coll = file_helper.create_data_coll(mdata, entries_df)
    times = [(time - mdata.start_time) / 3600 for time in data_coll.times]
    return times, data_coll.temp_diffs, data_coll.temps


def create_mean_power_time_graph(f_name, animate, fig, dims, is_cal, need_warning):
    """Create a mpl graph in a separate window."""
    if check_valid_file(f_name, is_cal):
        try:
            ax1 = fig.add_subplot(dims)

            if animate:
                _ = animation.FuncAnimation(
                    fig, __animate_mpt_graph, interval=1000, fargs=(f_name, ax1,))
            else:
                __animate_mpt_graph(0, f_name, ax1)
            return ax1
        except IndexError:
            if need_warning:
                __file_error(f_name)


def __animate_mpt_graph(i, f_name, axis):
    times, wavelen_diffs = __get_mean_power_diff_time_data(f_name)
    axis.clear()
    axis.set_title('Average Power (dBm) vs. Time (hr) from start', fontsize=12)
    axis.set_xlabel('Time (hr)')
    axis.set_ylabel('Power (dBm)')
    axis.plot(times, wavelen_diffs)


def __get_mean_power_diff_time_data(f_name):
    mdata, entries_df = file_helper.parse_csv_file(f_name)
    data_coll = file_helper.create_data_coll(mdata, entries_df)
    times = [(time - mdata.start_time) / 3600 for time in data_coll.times]
    return times, data_coll.mean_power_diffs


def create_indiv_waves_graph(f_name, animate, fig, dims, is_cal, need_warning):
    """Create individual wavelengths graph."""
    if check_valid_file(f_name, is_cal):
        try:
            #ax1 = plt.subplot2grid((10, 1), (1, 0), rowspan=7, colspan=1)
            #ax2 = plt.subplot2grid((10, 1), (8, 0), rowspan=2, colspan=1,
            #                       sharex=ax1)
            ax1 = fig.add_subplot(dims)

            ax2=None
            if animate:
                _ = animation.FuncAnimation(
                    fig, __animate_indiv_waves, interval=1000, fargs=(f_name, ax1, ax2,))
            else:
                __animate_indiv_waves(0, f_name, ax1, ax2)
            return ax1
        except IndexError:
            if need_warning:
                __file_error(f_name)


def __animate_indiv_waves(i, f_name, ax1, ax2):
    times, wavelens, wavelen_diffs, snums = __get_indiv_waves_data(f_name)
    ax1.clear()
    #ax2.clear()

    ax1.set_title('Raw Wavelengths vs. Time (hr)', fontsize=12)
    ax1.set_ylabel('Wavelength (pm)')
    ax1.set_xlabel('Time (hr)')

    #ax1 = plt.subplot2grid((10, 1), (1, 0), rowspan=7, colspan=1)
    #ax1.set_ylabel('Wavelength (nm)')
    #ax2 = plt.subplot2grid((10, 1), (8, 0), rowspan=2, colspan=1,
    #                       sharex=ax1)

    #ax2.set_xlabel('Time (hr)')
    #ax2.set_ylabel('{} Wavelength (pm)'.format(u'\u0394'))

    idx = 0
    axes = []
    for waves, wave_diffs, color in zip(wavelens, wavelen_diffs, file_helper.HEX_COLORS):
        axes.append(ax1.plot(times, waves, color=color)[0])
        #ax2.plot(times, wave_diffs, color=color)
        idx += 1

    #ax1.legend(axes, snums, loc='upper center', bbox_to_anchor=(0.5, -0.15),
    #      fancybox=True, shadow=True, ncol=int(len(snums) / 2 + 0.5), fontsize=8)
    #ax1.legend(axes, snums, bbox_to_anchor=(1, -1.25), loc='lower right', borderaxespad=0.,
    #           ncol=int(len(snums) / 2 + 0.5), fontsize=8)


def __get_indiv_waves_data(f_name):
    mdata, entries_df = file_helper.parse_csv_file(f_name)
    data_coll = file_helper.create_data_coll(mdata, entries_df)
    times = [(time - mdata.start_time) / 3600 for time in data_coll.times]
    return times, data_coll.wavelens, data_coll.wavelen_diffs, mdata.serial_nums


def create_indiv_powers_graph(f_name, animate, fig, dims, is_cal, need_warning):
    """Create individual wavelengths graph."""
    if check_valid_file(f_name, is_cal):
        try:
            #ax1 = plt.subplot2grid((10, 1), (1, 0), rowspan=7, colspan=1)
            #ax2 = plt.subplot2grid((10, 1), (8, 0), rowspan=2, colspan=1,
            #                       sharex=ax1)
            ax1 = fig.add_subplot(dims)
            ax2=None

            if animate:
                ani = animation.FuncAnimation(
                    fig, __animate_indiv_powers, interval=1000, fargs=(f_name, ax1, ax2,))
            else:
                __animate_indiv_powers(0, f_name, ax1, ax2)
            return ax1
        except IndexError:
            if need_warning:
                __file_error(f_name)


def __animate_indiv_powers(i, f_name, ax1, ax2):
    times, powers, power_diffs, snums = __get_indiv_powers_data(f_name)
    ax1.clear()
    #ax2.clear()

    ax1.set_title('Raw Powers (dBm) vs. Time (hr)', fontsize=12)

    #ax1 = plt.subplot2grid((10, 1), (1, 0), rowspan=7, colspan=1)
    ax1.set_ylabel('Power (dBm)')
    ax1.set_xlabel('Time (hr)')
    #ax2 = plt.subplot2grid((10, 1), (8, 0), rowspan=2, colspan=1,
    #                       sharex=ax1)

    #ax2.set_xlabel('Time (hr)')
    #ax2.set_ylabel('{} Power (dBm)'.format(u'\u0394'))

    idx = 0
    axes = []
    for pows, pow_diffs, color in zip(powers, power_diffs, file_helper.HEX_COLORS):
        axes.append(ax1.plot(times, pows, color=color)[0])
        #ax2.plot(times, pow_diffs, color=color)
        idx += 1

    #ax1.legend(axes, snums, loc='upper center', bbox_to_anchor=(0.5, -0.15),
    #      fancybox=True, shadow=True, ncol=int(len(snums) / 2 + 0.5), fontsize=8)
    #ax1.legend(axes, snums, bbox_to_anchor=(1, -1.25), loc='lower right', borderaxespad=0.,
    #           ncol=int(len(snums) / 2 + 0.5), fontsize=8)


def __get_indiv_powers_data(f_name):
    mdata, entries_df = file_helper.parse_csv_file(f_name)
    data_coll = file_helper.create_data_coll(mdata, entries_df)
    times = [(time - mdata.start_time) / 3600 for time in data_coll.times]
    return times, data_coll.powers, data_coll.power_diffs, mdata.serial_nums


def create_drift_rates_graph(f_name, animate, fig, dims, is_cal, need_warning):
    """Create drift rates graph."""
    if check_valid_file(f_name, is_cal):
        try:
            ax1 = fig.sub_plt(dims)
            #ax1 = plt.subplot2grid((10, 1), (1, 0), rowspan=7, colspan=1)
            #ax2 = plt.subplot2grid((10, 1), (8, 0), rowspan=2, colspan=1, sharex=ax1)

            ax2=None
            if animate:
                ani = animation.FuncAnimation(
                    fig, __animate_drift_rates, interval=1000, fargs=(f_name, ax1, ax2,))
            else:
                __animate_indiv_powers(0, f_name, ax1, ax2)
            return ax1
        except IndexError:
            if need_warning:
                __file_error(f_name)


def __animate_drift_rates(i, f_name, ax1, ax2):
    times, times_real, drates, drates_real = __get_drift_rates(f_name)
    ax1.clear()
    #ax2.clear()

    ax1.set_title('Average Drift Rates (mK/min) vs. Time (hr)', fontsize=12)
    #ax1 = plt.subplot2grid((10, 1), (1, 0), rowspan=7, colspan=1)
    ax1.set_ylabel('Average Drift Rate (mK/min)')
    #ax2 = plt.subplot2grid((10, 1), (8, 0), rowspan=2, colspan=1,sharex=ax1)

    ax1.set_xlabel('Time (hr)')
    #ax2.set_ylabel('{} Average Drift Rate (mK/min)'.format(u'\u0394'))

    ax1.plot(times, drates)
    #ax2.plot(times_real, drates_real)


def __get_drift_rates(f_name):
    mdata, entries_df = file_helper.parse_csv_file(f_name)
    data_coll = file_helper.create_data_coll(mdata, entries_df)
    times = [(time - mdata.start_time) / 3600 for time in data_coll.times]
    drates = data_coll.drift_rates

    drates_real = []
    times_real = []
    for time, drate, real_point in zip(times, drates, data_coll.drift_rates):
        if real_point:
            drates_real.append(drate)
            times_real.append(time)

    return times, times_real, drates, drates_real


def check_valid_file(f_name, is_cal):
    """Checks if the file is a valid formatted csv file."""
    ret_val = False
    if os.path.isfile(f_name):
        if platform.system() != 'Linux':
            os.chmod(f_name, stat.S_IRWXU)
        with open(f_name, "r") as check_file:
            ret_val = True
            line = check_file.readline()
            ret_val = True
            if not is_cal and line != "Metadata\n" and need_warning:
                messagebox.showwarning("Invalid File",
                                       "".join(["File was either not generated by ",
                                                "this program or was altered. The specified csv ",
                                                "file must be a valid file to view the graphs."]))
                ret_val = False
            elif is_cal and line != "Caldata\n" and need_warning:
                messagebox.showwarning("Invalid File",
                                       "".join(["File was either not generated by ",
                                                "this program or was altered. The specified csv ",
                                                "file must be a valid file to view the graphs."]))
                ret_val = False
        os.chmod(f_name, stat.S_IREAD)
    if not ret_val:
        prog = "baking"
        if is_cal:
            prog = "calibration"
        if need_warning:
            messagebox.showwarning("File doesn't exist.",
                               "".join(["Specified csv file doesn't exist, start the {} process "
                                        .format(prog), "to view the graphs."]))
    return ret_val


if __name__ == "__main__":
    # create_mean_wave_time_graph("kyton_out.csv", False)
    # create_wave_power_graph("kyton_out.csv", False)
    # create_temp_time_graph("kyton_out.csv", False)
    # create_mean_power_time_graph("kyton_out.csv", False)
    # create_indiv_waves_graph("kyton_out.csv", False)
    # create_indiv_powers_graph("kyton_out.csv", False)
    # create_drift_rates_graph("kyton_out.csv", False)
    pass
