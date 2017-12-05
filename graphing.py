"""Module to help with graphing."""
# pylint: disable=import-error, relative-import, unused-argument
# pylint: disable=superfluous-parens

import os
import stat
import platform
from tkinter import mbox as mbox
import matplotlib.animation as animation
from matplotlib import style
import matplotlib.gridspec as gridspec
import file_helper
style.use("kyton")


class Graph(object):
    """
    Class describes a specific graph that can be representted as a subplot or a main plot.
    """
    def __init__(self, title, xlabel, ylabels, animate_func, fig, dims, fname, is_cal):
        self.title = title
        self.is_cal = is_cal
        self.xlabel = xlabel
        self.ylabels = ylabels
        self.file_name = fname
        self.animate_func = animate_func
        self.sub_dims = dims[0]
        self.zoom_dims = dims[1:]
        self.fig = fig
        self.sub_axis = None
        self.anim = None
        self.zoom_axes = []
        self.show_sub()

    def pause(self):
        """Pauses the graph animation."""
        self.anim.event_source.stop()

    def play(self):
        """Plays the graph animation."""
        self.anim.event_source.start()

    def show_sub(self):
        """Show the graph as a subplot in the grid."""
        print("Show sub file name: {}".format(to_csv(self.file_name.get())))
        if self.anim is not None:
            self.anim.event_source.stop()

        for axis in self.zoom_axes:
            axis.cla()
        self.zoom_axes = []
        self.sub_axis = self.fig.add_subplot(self.sub_dims)
        self.anim = animation.FuncAnimation(
            self.fig, self.sub_graph, interval=1500)

    def sub_graph(self, _):
        """Graph the subplot."""
        self.sub_axis.clear()
        self.sub_axis.set_title(self.title, fontsize=12)
        self.sub_axis.set_xlabel(self.xlabel)
        self.sub_axis.set_ylabel(self.ylabels[0])
        if check_valid_file(self.file_name, self.is_cal):
            print("Animating {} ...".format(self.animate_func.__name__))
            self.animate_func(self.file_name, (self.sub_axis,))
        else:
            # Invalid File
            pass

    def show_main(self):
        """Show the graph as the main plot."""
        print("Show main file name: {}".format(to_csv(self.file_name.get())))
        self.anim.event_source.stop()
        if self.sub_axis is not None:
            self.sub_axis.cla()
        self.fig.clf()
        self.zoom_axes = []
        share = None
        for dim in self.zoom_dims:
            if share is None:
                if dim != 111:
                    share = self.fig.add_subplot(dim)
                    share.get_xticklabels()[1].set_visible(False)
                else:
                    share = self.fig.add_subplot(dim)
            else:
                share = self.fig.add_subplot(dim, sharex=share)
            self.zoom_axes.append(share)
        self.anim = animation.FuncAnimation(
            self.fig, self.main_graph, interval=1000)

    def main_graph(self, _):
        """Graph the main plot."""
        for axis in self.zoom_axes:
            axis.clear()
        self.zoom_axes[0].set_title(self.title, fontsize=18)
        if len(self.zoom_axes) > 1:
            self.zoom_axes[1].set_xlabel(self.xlabel)
        else:
            self.zoom_axes[0].set_xlabel(self.xlabel)
        for i, ylabel in enumerate(self.ylabels):
            self.zoom_axes[i].set_ylabel(ylabel)
        if check_valid_file(self.file_name, self.is_cal):
            self.animate_func(self.file_name, tuple(self.zoom_axes))
        else:
            # Invalid File
            pass


class Graphing(object):
    """Class used for graphing the individual Graph objects."""

    def __init__(self, fname, dims, is_cal, figure, canvas, toolbar, master):
        self.file_name = fname
        self.dimensions = dims
        self.is_cal = is_cal
        self.figure = figure
        self.canvas = canvas
        self.toolbar = toolbar
        self.graphs = []
        self.sub_axes = []
        self.is_playing = True
        self.master = master

        titles = ["Raw Wavelengths vs. Time", "Power (dBm) vs. Wavelength (nm)",
                  "Raw Powers vs. Time", "Raw Temperature vs. Time from start",
                  "Average Power vs. Time from start",
                  "Average {} Wavelength vs. Time from start".format(u'\u0394')]
        xlabels = ["Time (hr)", "Wavelength (nm)", "Time (hr)",
                   "Time (hr)", "Time (hr)", "Time (hr)"]
        ylabels = [("Wavelength (pm)", "{} Wavelength (pm)".format(u'\u0394')), ("Power (dBm)",),
                   ("Power (dBm)", "{} Power (dBm)".format(u'\u0394')),
                   ("Temperature (K)", "{} Temperature (K)".format(u'\u0394')),
                   ("Power (dBm)",), ("Wavelength (pm)",)]
        animate_funcs = [animate_indiv_waves, animate_wp_graph, animate_indiv_powers,
                         animate_temp_graph, animate_mpt_graph, animate_mwt_graph]

        gs1 = gridspec.GridSpec(10, 1)
        reg_dims1 = (gs1[1:7, :])
        reg_dims2 = (gs1[7:10, :])
        reg_dims = (reg_dims1, reg_dims2)
        split_dims1 = (gs1[1:6, :])
        split_dims2 = (gs1[6:10, :])
        split_dims = (split_dims1, split_dims2)
        dimens = [reg_dims, (111,), reg_dims, split_dims, (111,), (111,)]
        if self.is_cal:
            titles.append("Average Drift Rate vs.Time")
            xlabels.append("Time (hr)")
            ylabels.append(("Average Drift Rate (mK/min)",
                            "{} Average Drift Rate (mK/min)".format(u'\u0394')))
            animate_funcs.append(animate_drift_rates)
            dims.append(reg_dims)

        # Create the graph objects and sub plot objects.
        for i, (title, xlbl, ylbl, anim, dimen) in \
                enumerate(zip(titles, xlabels, ylabels, animate_funcs, dimens)):
            dim_list = [self.dimensions + i + 1]
            for dim in dimen:
                dim_list.append(dim)
            temp = Graph(title, xlbl, ylbl, anim, self.figure,
                         dim_list, self.file_name, self.is_cal)
            self.graphs.append(temp)
            self.sub_axes.append(temp.sub_axis)
        # Setup double click for graphs."""
        self.cid = self.canvas.mpl_connect('button_press_event', self.show_main_plot)

        # Display the canvas and toolbar
        self.canvas.draw()
        self.toolbar.update()

    def update_axes(self):
        """Update the axes to include the sub plots on the graphing page."""
        self.sub_axes = []
        for graph in self.graphs:
            self.sub_axes.append(graph.sub_axis)

    def pause(self):
        """Pause animation for all the graphs."""
        self.is_playing = False
        for graph in self.graphs:
            graph.pause()

    def play(self):
        """Play animation for all the graphs."""
        self.is_playing = True
        for graph in self.graphs:
            graph.play()

    def __file_error(self):
        mbox.showwarning("File Error", "Inconsistency in the number of reading being" +
                         "stored in file {}.".format(self.file_name.get()))

    def show_subplots(self, event=None):
        """Show all the subplots in the graphing page."""
        # Need to check to make sure Csv is populated, if it is then get axes from graph_helper
        if event is None or event.dblclick:
            self.figure.clf()
            for graph in self.graphs:
                graph.show_sub()

            self.canvas.mpl_disconnect(self.cid)
            self.cid = self.canvas.mpl_connect('button_press_event', self.show_main_plot)
            self.canvas.draw()
            self.toolbar.update()
            if not self.is_playing:
                self.master.after(1500, self.pause)

    def show_main_plot(self, event):
        """Show the main plot on the graphing page."""
        self.update_axes()
        for i, axis in enumerate(self.sub_axes):
            if event.dblclick and axis == event.inaxes:
                self.graphs[i].show_main()
                self.canvas.mpl_disconnect(self.cid)
                self.cid = self.canvas.mpl_connect('button_press_event', self.show_subplots)
                self.canvas.draw()
                self.toolbar.update()
                if not self.is_playing:
                    self.master.after(1500, self.pause)


def animate_mwt_graph(f_name, axes):
    """Animate function for the mean wavelength vs. time graph."""
    times, wavelen_diffs = __get_mean_wave_diff_time_data(f_name)
    axes[0].plot(times, wavelen_diffs)


def __get_mean_wave_diff_time_data(f_name):
    print("Get_mean_wave_diff_time_data f_name: {}".format(to_csv(f_name.get())))
    if platform.system() != 'Linux':
        os.chmod(to_csv(f_name.get()), stat.S_IRWXU)
    mdata, entries_df = file_helper.parse_csv_file(to_csv(f_name.get()))
    if platform.system() != 'Linux':
        os.chmod(to_csv(f_name.get()), stat.S_IREAD)
    data_coll = file_helper.create_data_coll(mdata, entries_df)
    times = [(time - mdata.start_time) / 3600 for time in data_coll.times]
    return times, data_coll.mean_wavelen_diffs


def animate_wp_graph(f_name, axis):
    """Animate function for the wavelength vs. power graph."""
    wavelens, powers, snums = __get_wave_power_graph(f_name)
    idx = 0
    axes = []
    for waves, powers, color in zip(wavelens, powers, file_helper.HEX_COLORS):
        axes.append(axis[0].scatter(waves, powers, color=color, s=75))
        idx += 1

    font_size = 8
    if platform.system() == "Linux":
        font_size = 10
    legend = axis[0].legend(axes, snums, bbox_to_anchor=(.5, 1.25), loc='upper center',
                            ncol=int(len(snums) / 2 + 0.5), fontsize=font_size,
                            fancybox=True, shadow=True)
    for text in legend.get_texts():
        text.set_color("black")


def __get_wave_power_graph(f_name):
    mdata, entries_df = file_helper.parse_csv_file(to_csv(f_name.get()))
    data_coll = file_helper.create_data_coll(mdata, entries_df)
    return data_coll.wavelens, data_coll.powers, mdata.serial_nums


def animate_temp_graph(f_name, axes):
    """Animate function for the temperature graph."""
    times, temp_diffs, temps = __get_temp_time_graph(f_name)
    axes[0].plot(times, temps)
    if len(axes) > 1:
        axes[1].plot(times, temp_diffs, color='b')


def __get_temp_time_graph(f_name):
    mdata, entries_df = file_helper.parse_csv_file(to_csv(f_name.get()))
    data_coll = file_helper.create_data_coll(mdata, entries_df)
    times = [(time - mdata.start_time) / 3600 for time in data_coll.times]
    return times, data_coll.temp_diffs, data_coll.temps


def animate_mpt_graph(f_name, axis):
    """Animate function for the mean power vs. time graph."""
    times, wavelen_diffs = __get_mean_power_diff_time_data(f_name)
    axis[0].plot(times, wavelen_diffs)


def __get_mean_power_diff_time_data(f_name):
    mdata, entries_df = file_helper.parse_csv_file(to_csv(f_name.get()))
    data_coll = file_helper.create_data_coll(mdata, entries_df)
    times = [(time - mdata.start_time) / 3600 for time in data_coll.times]
    return times, data_coll.mean_power_diffs


def animate_indiv_waves(f_name, axis):
    """Animate function for the individual wavelengths graph."""
    times, wavelens, wavelen_diffs, snums = __get_indiv_waves_data(f_name)
    idx = 0
    axes = []
    for waves, wave_diffs, color in zip(wavelens, wavelen_diffs, file_helper.HEX_COLORS):
        axes.append(axis[0].plot(times, waves, color=color)[0])
        if len(axis) > 1:
            axis[1].plot(times, wave_diffs, color=color)
        idx += 1

    if len(axis) > 1:
        font_size = 8
        if platform.system() == "Linux":
            font_size = 10
        legend = axis[0].legend(axes, snums, bbox_to_anchor=(.5, 1.25), loc='upper center',
                                ncol=int(len(snums) / 2 + 0.5), fontsize=font_size,
                                fancybox=True, shadow=True)
        for text in legend.get_texts():
            text.set_color("black")


def __get_indiv_waves_data(f_name):
    mdata, entries_df = file_helper.parse_csv_file(to_csv(f_name.get()))
    data_coll = file_helper.create_data_coll(mdata, entries_df)
    times = [(time - mdata.start_time) / 3600 for time in data_coll.times]
    return times, data_coll.wavelens, data_coll.wavelen_diffs, mdata.serial_nums


def animate_indiv_powers(f_name, axis):
    """Animate function for the individual powers graph."""
    times, powers, power_diffs, snums = __get_indiv_powers_data(f_name)
    idx = 0
    axes = []
    for pows, pow_diffs, color in zip(powers, power_diffs, file_helper.HEX_COLORS):
        axes.append(axis[0].plot(times, pows, color=color)[0])
        if len(axis) > 1:
            axis[1].plot(times, pow_diffs, color=color)
        idx += 1

    if len(axis) > 1:
        font_size = 8
        if platform.system() == "Linux":
            font_size = 10

        legend = axis[0].legend(axes, snums, bbox_to_anchor=(.5, 1.25), loc='upper center',
                                ncol=int(len(snums) / 2 + 0.5), fontsize=font_size,
                                fancybox=True, shadow=True)
        for text in legend.get_texts():
            text.set_color("black")


def __get_indiv_powers_data(f_name):
    mdata, entries_df = file_helper.parse_csv_file(to_csv(f_name.get()))
    data_coll = file_helper.create_data_coll(mdata, entries_df)
    times = [(time - mdata.start_time) / 3600 for time in data_coll.times]
    return times, data_coll.powers, data_coll.power_diffs, mdata.serial_nums


def animate_drift_rates(f_name, axes):
    """Animate function for the drift rates graph."""
    times, times_real, drates, drates_real = __get_drift_rates(f_name)
    axes[0].plot(times, drates)
    if len(axes) > 1:
        axes[1].plot(times_real, drates_real)


def __get_drift_rates(f_name):
    mdata, entries_df = file_helper.parse_csv_file(to_csv(f_name.get()))
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
    if os.path.isfile(f_name.get()):
        if platform.system() != 'Linux':
            os.chmod(f_name.get(), stat.S_IRWXU)
        with open(f_name.get(), "r") as check_file:
            line = check_file.readline()
            ret_val = True
            if not is_cal and line != "Metadata\n":
                mbox.showwarning("Invalid File",
                                 "".join(["File was either not generated by ",
                                          "this program or was altered. The specified csv ",
                                          "file must be a valid file to view the graphs."]))
                ret_val = False
            elif is_cal and line != "Caldata\n":
                mbox.showwarning("Invalid File",
                                 "".join(["File was either not generated by ",
                                          "this program or was altered. The specified csv ",
                                          "file must be a valid file to view the graphs."]))
                ret_val = False
        os.chmod(f_name.get(), stat.S_IREAD)
    if not ret_val:
        prog = "baking"
        if is_cal:
            prog = "calibration"
        if False:  # need_warning: # pylint: disable=using-constant-test
            mbox.showwarning("File doesn't exist.",
                             "".join(["Specified csv file doesn't exist, start the {} process "
                                      .format(prog), "to view the graphs."]))
    return ret_val


def to_csv(xcel_file):
    """Convert the excel file name to a csv file name."""
    temp = xcel_file.split(".")[0]
    return "{}.csv".format(temp)
