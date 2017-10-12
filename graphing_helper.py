"""Module to help with graphing."""
# pylint: disable=import-error, relative-import, unused-argument

import os
import stat
from tkinter import messagebox
import matplotlib.animation as animation
from matplotlib import style
import matplotlib.pyplot as plt
import file_helper

style.use("ggplot")


def __file_error(f_name):
    messagebox. \
        showwarning("File Error", "Inconsistency in the number of reading being stored in file {}."
                    .format(f_name))


def create_mean_wave_time_graph(f_name, animate, is_cal=False):
    """Create a mpl graph in a separate window."""
    if check_valid_file(f_name, is_cal):
        try:
            fig = plt.figure(0, figsize=(8, 6))
            ax1 = fig.add_subplot(1, 1, 1)

            plt.xlabel('Time (hr)')
            plt.ylabel('Wavelength (pm)')
            fig.suptitle(
                'Average {} (pm) vs. Time (hr) from start'.format(u'\u0394\u03BB'))

            if animate:
                ani = animation.FuncAnimation(fig, __animate_mwt_graph,
                                              interval=1000, fargs=(f_name, ax1,))
                fig.show()
            else:
                __animate_mwt_graph(0, f_name, ax1)
                plt.show()
        except IndexError:
            __file_error(f_name)


def __animate_mwt_graph(i, f_name, axis):
    times, wavelen_diffs = __get_mean_wave_diff_time_data(f_name)
    axis.clear()
    plt.xlabel('Time (hr)')
    plt.ylabel('Wavelength (pm)')
    axis.plot(times, wavelen_diffs)


def __get_mean_wave_diff_time_data(f_name):
    mdata, entries_df = file_helper.parse_csv_file(f_name)
    data_coll = file_helper.create_data_coll(mdata, entries_df)
    times = [(time - mdata.start_time) / 3600 for time in data_coll.times]
    return times, data_coll.mean_wavelen_diffs


def create_wave_power_graph(f_name, animate, is_cal=False):
    """Creates the wavelength vs. power graph."""
    if check_valid_file(f_name, is_cal):
        try:
            fig = plt.figure(1, figsize=(8, 6))
            ax1 = fig.add_subplot(1, 1, 1)
            fig.suptitle('Power (dBm) vs. Wavelength (nm)')

            if animate:
                ani = animation.FuncAnimation(fig, __animate_wp_graph,
                                              interval=1000, fargs=(f_name, ax1,))
                fig.show()
            else:
                __animate_wp_graph(0, f_name, ax1)
                plt.show()
        except IndexError:
            __file_error(f_name)


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

    axis.legend(axes, snums, bbox_to_anchor=(1.10, 1.10), loc='upper right', borderaxespad=0.,
                ncol=int(len(snums) / 2 + 0.5), fontsize=8)


def __get_wave_power_graph(f_name):
    mdata, entries_df = file_helper.parse_csv_file(f_name)
    data_coll = file_helper.create_data_coll(mdata, entries_df)

    return data_coll.wavelens, data_coll.powers, mdata.serial_nums


def create_temp_time_graph(f_name, animate, is_cal=False):
    """Creates the temperature vs. time graph."""
    if check_valid_file(f_name, is_cal):
        try:
            fig = plt.figure(2, figsize=(8, 6))

            ax1 = plt.subplot2grid((10, 1), (1, 0), rowspan=5, colspan=1)
            plt.ylabel('Temperature (K)')
            ax2 = plt.subplot2grid((10, 1), (6, 0), rowspan=4, colspan=1,
                                   sharex=ax1)

            fig.suptitle(
                'Raw Temperature (K) vs. Time (hr) from start.')
            plt.ylabel('{} Temperature (K)'.format(u'\u0394'))
            plt.xlabel('Time (hr)')

            if animate:
                ani = animation.FuncAnimation(
                    fig, __animate_temp_graph, interval=1000, fargs=(f_name, ax1, ax2, ))
                fig.show()
            else:
                __animate_temp_graph(0, f_name, ax1, ax2)
                plt.show()
        except IndexError:
            __file_error(f_name)


def __animate_temp_graph(i, f_name, ax1, ax2):
    times, temp_diffs, temps = __get_temp_time_graph(f_name)
    ax1.clear()
    ax2.clear()

    ax1 = plt.subplot2grid((10, 1), (0, 0), rowspan=7, colspan=1)
    plt.ylabel('Temperature (K)')
    ax2 = plt.subplot2grid((10, 1), (7, 0), rowspan=3, colspan=1,
                           sharex=ax1)

    plt.xlabel('Time (hr)')
    plt.ylabel('{} Temperature (K)'.format(u'\u0394'))
    ax1.plot(times, temps)
    ax2.plot(times, temp_diffs, color='b')


def __get_temp_time_graph(f_name):
    mdata, entries_df = file_helper.parse_csv_file(f_name)
    data_coll = file_helper.create_data_coll(mdata, entries_df)
    times = [(time - mdata.start_time) / 3600 for time in data_coll.times]
    return times, data_coll.temp_diffs, data_coll.temps


def create_mean_power_time_graph(f_name, animate, is_cal=False):
    """Create a mpl graph in a separate window."""
    if check_valid_file(f_name, is_cal):
        try:
            fig = plt.figure(3, figsize=(8, 6))
            ax1 = fig.add_subplot(1, 1, 1)

            plt.xlabel('Time (hr)')
            plt.ylabel('Power (dBm)')
            fig.suptitle('Average Power (dBm) vs. Time (hr) from start')

            if animate:
                ani = animation.FuncAnimation(
                    fig, __animate_mpt_graph, interval=1000, fargs=(f_name, ax1,))
                fig.show()
            else:
                __animate_mpt_graph(0, f_name, ax1)
                plt.show()
        except IndexError:
            __file_error(f_name)


def __animate_mpt_graph(i, f_name, axis):
    times, wavelen_diffs = __get_mean_power_diff_time_data(f_name)
    axis.clear()
    plt.xlabel('Time (hr)')
    plt.ylabel('Power (dBm)')
    axis.plot(times, wavelen_diffs)


def __get_mean_power_diff_time_data(f_name):
    mdata, entries_df = file_helper.parse_csv_file(f_name)
    data_coll = file_helper.create_data_coll(mdata, entries_df)
    times = [(time - mdata.start_time) / 3600 for time in data_coll.times]
    return times, data_coll.mean_power_diffs


def create_indiv_waves_graph(f_name, animate, is_cal=False):
    """Create individual wavelengths graph."""
    if check_valid_file(f_name, is_cal):
        try:
            fig = plt.figure(4, figsize=(8, 6))

            ax1 = plt.subplot2grid((10, 1), (1, 0), rowspan=7, colspan=1)
            plt.ylabel('Wavelength (nm)')
            ax2 = plt.subplot2grid((10, 1), (8, 0), rowspan=2, colspan=1,
                                   sharex=ax1)

            plt.xlabel('Time (hr)')
            plt.ylabel('Wavelength (pm)')
            fig.suptitle('Raw Wavelengths vs. Time (hr)')

            if animate:
                ani = animation.FuncAnimation(
                    fig, __animate_indiv_waves, interval=1000, fargs=(f_name, ax1, ax2,))
                fig.show()
            else:
                __animate_indiv_waves(0, f_name, ax1, ax2)
                plt.show()
        except IndexError:
            __file_error(f_name)


def __animate_indiv_waves(i, f_name, ax1, ax2):
    times, wavelens, wavelen_diffs, snums = __get_indiv_waves_data(f_name)
    ax1.clear()
    ax2.clear()

    ax1 = plt.subplot2grid((10, 1), (1, 0), rowspan=7, colspan=1)
    plt.ylabel('Wavelength (nm)')
    ax2 = plt.subplot2grid((10, 1), (8, 0), rowspan=2, colspan=1,
                           sharex=ax1)

    plt.xlabel('Time (hr)')
    plt.ylabel('{} Wavelength (pm)'.format(u'\u0394'))

    idx = 0
    axes = []
    for waves, wave_diffs, color in zip(wavelens, wavelen_diffs, file_helper.HEX_COLORS):
        axes.append(ax1.plot(times, waves, color=color)[0])
        ax2.plot(times, wave_diffs, color=color)
        idx += 1

    ax1.legend(axes, snums, bbox_to_anchor=(1.10, 1.25), loc='upper right', borderaxespad=0.,
               ncol=int(len(snums) / 2 + 0.5), fontsize=8)


def __get_indiv_waves_data(f_name):
    mdata, entries_df = file_helper.parse_csv_file(f_name)
    data_coll = file_helper.create_data_coll(mdata, entries_df)
    times = [(time - mdata.start_time) / 3600 for time in data_coll.times]
    return times, data_coll.wavelens, data_coll.wavelen_diffs, mdata.serial_nums


def create_indiv_powers_graph(f_name, animate, is_cal=False):
    """Create individual wavelengths graph."""
    if check_valid_file(f_name, is_cal):
        try:
            fig = plt.figure(5, figsize=(8, 6))

            ax1 = plt.subplot2grid((10, 1), (1, 0), rowspan=7, colspan=1)
            plt.ylabel('Power (dBm)')
            ax2 = plt.subplot2grid((10, 1), (8, 0), rowspan=2, colspan=1,
                                   sharex=ax1)

            plt.xlabel('Time (hr)')
            plt.ylabel('{} Power (dBm)'.format(u'\u0394'))
            fig.suptitle('Raw Powers (dBm) vs. Time (hr)')

            if animate:
                ani = animation.FuncAnimation(
                    fig, __animate_indiv_powers, interval=1000, fargs=(f_name, ax1, ax2,))
                fig.show()
            else:
                __animate_indiv_powers(0, f_name, ax1, ax2)
                plt.show()
        except IndexError:
            __file_error(f_name)


def __animate_indiv_powers(i, f_name, ax1, ax2):
    times, powers, power_diffs, snums = __get_indiv_powers_data(f_name)
    ax1.clear()
    ax2.clear()

    ax1 = plt.subplot2grid((10, 1), (1, 0), rowspan=7, colspan=1)
    plt.ylabel('Power (dBm)')
    ax2 = plt.subplot2grid((10, 1), (8, 0), rowspan=2, colspan=1,
                           sharex=ax1)

    plt.xlabel('Time (hr)')
    plt.ylabel('{} Power (dBm)'.format(u'\u0394'))

    idx = 0
    axes = []
    for pows, pow_diffs, color in zip(powers, power_diffs, file_helper.HEX_COLORS):
        axes.append(ax1.plot(times, pows, color=color)[0])
        ax2.plot(times, pow_diffs, color=color)
        idx += 1

    ax1.legend(axes, snums, bbox_to_anchor=(1.10, 1.25), loc='upper right', borderaxespad=0.,
               ncol=int(len(snums) / 2 + 0.5), fontsize=8)


def __get_indiv_powers_data(f_name):
    mdata, entries_df = file_helper.parse_csv_file(f_name)
    data_coll = file_helper.create_data_coll(mdata, entries_df)
    times = [(time - mdata.start_time) / 3600 for time in data_coll.times]
    return times, data_coll.powers, data_coll.power_diffs, mdata.serial_nums


def create_drift_rates_graph(f_name, animate, is_cal=False):
    """Create drift rates graph."""
    if check_valid_file(f_name, is_cal):
        try:
            fig = plt.figure(6, figsize=(8, 6))

            ax1 = plt.subplot2grid((10, 1), (1, 0), rowspan=7, colspan=1)
            plt.ylabel('Average Drift Rate (mK/min)')
            ax2 = plt.subplot2grid((10, 1), (8, 0), rowspan=2, colspan=1,
                                   sharex=ax1)

            plt.xlabel('Time (hr)')
            plt.ylabel('Average Drift Rate (mK/min)')
            fig.suptitle('Average Drift Rates (mK/min) vs. Time (hr)')

            if animate:
                ani = animation.FuncAnimation(
                    fig, __animate_drift_rates, interval=1000, fargs=(f_name, ax1, ax2,))
                fig.show()
            else:
                __animate_indiv_powers(0, f_name, ax1, ax2)
                plt.show()
        except IndexError:
            __file_error(f_name)


def __animate_drift_rates(i, f_name, ax1, ax2):
    times, times_real, drates, drates_real = __get_drift_rates(f_name)
    ax1.clear()
    ax2.clear()

    ax1 = plt.subplot2grid((10, 1), (1, 0), rowspan=7, colspan=1)
    plt.ylabel('Average Drift Rate (mK/min)')
    ax2 = plt.subplot2grid((10, 1), (8, 0), rowspan=2, colspan=1,
                           sharex=ax1)

    plt.xlabel('Time (hr)')
    plt.ylabel('{} Average Drift Rate (mK/min)'.format(u'\u0394'))

    ax1.plot(times, drates)
    ax2.plot(times_real, drates_real)


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
        os.chmod(f_name, stat.S_IRWXU)
        with open(f_name, "r") as check_file:
            line = check_file.readline()
            ret_val = True
            if not is_cal and line != "Metadata\n":
                messagebox.showwarning("Invalid File",
                                       "".join(["File was either not generated by ",
                                                "this program or was altered. The specified csv ",
                                                "file must be a valid file to view the graphs."]))
                ret_val = False
            elif is_cal and line != "Caldata\n":
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
