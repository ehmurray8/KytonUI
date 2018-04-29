import gc
import os
import uuid
import threading
from tkinter import StringVar
from typing import Tuple, List, Callable, Any, Union
import time
from fbgui import file_helper as fh
import matplotlib.animation as animation
import matplotlib.gridspec as gridspec
from fbgui.constants import HEX_COLORS, BAKING, CAL, DB_PATH
import matplotlib.ticker as mtick
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib import style
from matplotlib.figure import Figure
import numpy as np
from graph_toolbar import Toolbar
from fbgui.data_container import DataCollection
from fbgui import helpers

style.use("kyton")


class Graph(object):
    """
    Class describes a specific graph that can be represented as a subplot or a main plot.
    """
    def __init__(self, title: str, xlabel: str, ylabels: Tuple[str], animate_func: Callable, fig: Figure,
                 dims: List[Union[int, Any]], fname: StringVar, is_cal: bool, snums: List[str]):
        self.title = title
        self.is_cal = is_cal
        self.xlabel = xlabel
        self.ylabels = ylabels
        self.file_name = fname
        self.sub_dims = dims[0]
        self.zoom_dims = dims[1:]
        self.animate_func = animate_func
        self.fig = fig
        self.sub_axis = None
        self.anim = None
        self.snums = snums
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
        if self.anim is not None:
            self.anim.event_source.stop()

        for axis in self.zoom_axes:
            axis.cla()
        self.zoom_axes = []
        self.sub_axis = self.fig.add_subplot(self.sub_dims)
        self.anim = animation.FuncAnimation(self.fig, self.sub_graph, interval=7500, save_count=0)

    def sub_graph(self, _):
        """Graph the subplot."""
        self.sub_axis.clear()
        gc.collect()
        self.sub_axis.set_title(self.title, fontsize=12)
        self.sub_axis.set_xlabel(self.xlabel)
        self.sub_axis.set_ylabel(self.ylabels[0])
        axes_tuple = (self.sub_axis,)
        self.check_val_file(axes_tuple)

    def check_val_file(self, axes_tuple):
        name = os.path.splitext(os.path.split(self.file_name.get())[1])[0]
        conn = fh.sqlite3.connect(DB_PATH)
        cur = conn.cursor()
        func = BAKING
        if self.is_cal:
            func = CAL
        if fh.program_exists(name, cur, func):
            conn.close()
            self.animate_func(axes_tuple, self.snums, self.is_cal)
        else:
            conn.close()

    def show_main(self):
        """Show the graph as the main plot."""
        self.anim.event_source.stop()
        if self.sub_axis is not None:
            self.sub_axis.cla()
        self.zoom_axes = []
        share = None
        for dim in self.zoom_dims:
            if share is None:
                if dim != 111:
                    share = self.fig.add_subplot(dim)
                    share.get_xticklabels()[1].set_visible(False)
                    share.get_xaxis().set_visible(False)
                else:
                    share = self.fig.add_subplot(dim)
            else:
                share = self.fig.add_subplot(dim, sharex=share)
            self.zoom_axes.append(share)
        self.anim = animation.FuncAnimation(self.fig, self.main_graph, interval=7500, save_count=0)

    def main_graph(self, _):
        """Graph the main plot."""
        try:
            for axis in self.zoom_axes:
                axis.clear()
            gc.collect()
            self.zoom_axes[0].set_title(self.title, fontsize=18)
            if len(self.zoom_axes) > 1:
                self.zoom_axes[1].set_xlabel(self.xlabel)
                self.zoom_axes[1].xaxis.label.set_fontsize(16)
            else:
                self.zoom_axes[0].set_xlabel(self.xlabel)
                self.zoom_axes[0].xaxis.label.set_fontsize(16)
            for i, ylabel in enumerate(self.ylabels):
                self.zoom_axes[i].set_ylabel(ylabel)
                self.zoom_axes[i].yaxis.label.set_fontsize(16)

            axes_tuple = tuple(self.zoom_axes)
            self.check_val_file(axes_tuple)
        except IndexError:
            # Issue with cleaning thread and double tap
            pass


class Graphing(object):
    """Class used for graphing the individual Graph objects."""

    data_coll: DataCollection = None
    data_coll_cal: DataCollection = None

    def __init__(self, fname: StringVar, dims: List[Union[int, Any]], is_cal: bool, figure: Figure,
                 canvas: FigureCanvasTkAgg, toolbar: Toolbar, master, snums: List[str]):
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
        self.snums = snums

        threading.Thread(target=self.update_data_coll).start()

        titles = ["Wavelengths vs. Time", "Power vs. Wavelength", "Powers vs. Time", "Temperature vs. Time",
                  "Average Power vs. Time", "Average Wavelength vs. Time"]
        xlabels = ["Time (hr)", "Wavelength (nm)", "Time (hr)", "Time (hr)", "Time (hr)", "Time (hr)"]
        ylabels = [("{} Wavelength (pm)".format(u'\u0394'), "Wavelength (nm)"), ("Power (dBm)",),
                   ("{} Power (dBm)".format(u'\u0394'), "Power (dBm)"),
                   ("{} Temperature (K)".format(u'\u0394'), "Temperature (K)"),
                   ("Average {} Power (dBm)".format(u"\u0394"),), ("{} Wavelength (pm)".format(u'\u0394'),)]
        animate_funcs = [wave_graph, wave_power_graph, power_graph,
                         temp_graph, average_power_graph, average_wave_graph]

        gs1 = gridspec.GridSpec(10, 1)
        reg_dims1 = (gs1[1:7, :])
        reg_dims2 = (gs1[7:10, :])
        reg_dims = (reg_dims1, reg_dims2)
        split_dims1 = (gs1[1:6, :])
        split_dims2 = (gs1[6:10, :])
        split_dims = (split_dims1, split_dims2)
        mid_dims = ((gs1[1:9, :]), )
        dimens = [reg_dims, mid_dims, reg_dims, split_dims, (111,), (111,)]
        if self.is_cal:
            titles[2] = "Drift Rate vs.Time"
            xlabels[2] = "Time (hr)"
            ylabels[2] = ("Drift Rate (mK/min)", "{} Drift Rate (mK/min)".format(u'\u0394'))
            animate_funcs[2] = drift_rate_graph

        # Create the graph objects and sub plot objects.
        for i, (title, xlbl, ylbl, anim, dimen) in enumerate(zip(titles, xlabels, ylabels, animate_funcs, dimens)):
            dim_list = [self.dimensions + i + 1]
            for dim in dimen:
                dim_list.append(dim)
            temp = Graph(title, xlbl, ylbl, anim, self.figure, dim_list, self.file_name, self.is_cal, self.snums)
            self.graphs.append(temp)
            self.sub_axes.append(temp.sub_axis)
        # Setup double click for graphs."""
        self.cid = self.canvas.mpl_connect('button_press_event', self.show_main_plot)

        # Display the canvas and toolbar
        self.canvas.draw()
        self.toolbar.update()

    def update_data_coll(self):
        thread_id = uuid.uuid4()
        print("Opening new graph thread: {}".format(thread_id))
        self.master.thread_map[thread_id] = True
        self.master.graph_threads.append(thread_id)
        while self.master.thread_map[thread_id]:
            try:
                name = helpers.get_file_name(self.file_name.get())
                if self.is_cal:
                    Graphing.data_coll_cal = fh.create_data_coll(name, self.is_cal)[0]
                else:
                    Graphing.data_coll = fh.create_data_coll(name, self.is_cal)[0]
            except RuntimeError:
                pass
            time.sleep(8)

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

    def show_subplots(self, event=None):
        """Show all the subplots in the graphing page."""
        # Need to check to make sure Csv is populated
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
        if isinstance(event, int):
            self.figure.clf()
            self.graphs[event].show_main()
            self.canvas.mpl_disconnect(self.cid)
            self.cid = self.canvas.mpl_connect('button_press_event', self.show_subplots)
            self.canvas.draw()
            self.toolbar.update()
            if not self.is_playing:
                self.master.after(1500, self.pause)
        else:
            for i, axis in enumerate(self.sub_axes):
                if event.dblclick and axis == event.inaxes:
                    self.figure.clf()
                    self.graphs[i].show_main()
                    self.canvas.mpl_disconnect(self.cid)
                    self.cid = self.canvas.mpl_connect('button_press_event', self.show_subplots)
                    self.canvas.draw()
                    self.toolbar.update()
                    if not self.is_playing:
                        self.master.after(1500, self.pause)


def animate_graph(use_snums):
    def _animate_graph(func):
        def _wrapper(axes, snums, is_cal):
            dc = Graphing.data_coll
            if is_cal:
                dc = Graphing.data_coll_cal
            if dc is not None:
                if use_snums:
                    if snums is not None and not len(snums):
                        snums = fh.get_snums(is_cal)
                    func(axes, snums, dc)
                else:
                    func(axes, dc)
        return _wrapper
    return _animate_graph


@animate_graph(False)
def average_wave_graph(axes, dc):
    """Animate function for the mean wavelength vs. time graph."""
    times, wavelen_diffs = dc.times, dc.mean_wavelen_diffs
    axes[0].plot(times, wavelen_diffs)


@animate_graph(True)
def wave_power_graph(axis, snums, dc):
    """Animate function for the wavelength vs. power graph."""
    wavelens, powers = dc.wavelens, dc.powers
    idx = 0
    axes = []
    for waves, powers, color in zip(wavelens, powers, HEX_COLORS):
        axes.append(axis[0].scatter(waves, powers, color=color, s=75))
        idx += 1

    font_size = 8
    legend = axis[0].legend(axes, snums, bbox_to_anchor=(.5, 1.25), loc='upper center',
                            ncol=int(len(snums) / 2 + 0.5),
                            fontsize=font_size, fancybox=True, shadow=True)
    for text in legend.get_texts():
        text.set_color("black")


@animate_graph(True)
def temp_graph(axes, _, dc):
    """Animate function for the temperature graph."""
    times, temp_diffs, temps = dc.times, dc.temp_diffs, dc.temps
    axes[0].plot(times, temp_diffs)
    if len(axes) > 1:
        axes[1].plot(times, temps, color='b')


@animate_graph(False)
def average_power_graph(axis, dc):
    """Animate function for the mean power vs. time graph."""
    times, power_diffs = dc.times, dc.mean_power_diffs
    axis[0].yaxis.set_major_formatter(mtick.FuncFormatter(formatter))
    axis[0].plot(times, power_diffs)


@animate_graph(True)
def wave_graph(axis, snums, dc):
    """Animate function for the individual wavelengths graph."""
    times, wavelens, wavelen_diffs = dc.times, dc.wavelens, dc.wavelen_diffs
    wavelen_diffs = [w * 1000 for w in wavelen_diffs]
    idx = 0
    axes = []
    for waves, wave_diffs, color in zip(wavelens, wavelen_diffs, HEX_COLORS):
        axes.append(axis[0].plot(times, wave_diffs, color=color)[0])
        if len(axis) > 1:
            axis[1].plot(times, waves, color=color)
        idx += 1

    if len(axis) > 1:
        font_size = 8
        legend = axis[0].legend(axes, snums, bbox_to_anchor=(.5, 1.25), loc='upper center',
                                ncol=int(len(snums) / 2 + 0.5), fontsize=font_size, fancybox=True, shadow=True)
        for text in legend.get_texts():
            text.set_color("black")


@animate_graph(True)
def power_graph(axis, snums, dc):
    """Animate function for the individual powers graph."""
    times, powers, power_diffs = dc.times, dc.powers, dc.power_diffs
    idx = 0
    axes = []
    for pows, pow_diffs, color in zip(powers, power_diffs, HEX_COLORS):
        axes.append(axis[0].plot(times, pow_diffs, color=color)[0])
        if len(axis) > 1:
            axis[1].plot(times, pows, color=color)
        idx += 1

    if len(axis) > 1:
        font_size = 8
        legend = axis[0].legend(axes, snums, bbox_to_anchor=(.5, 1.25), loc='upper center',
                                ncol=int(len(snums) / 2 + 0.5), fontsize=font_size, fancybox=True, shadow=True)
        for text in legend.get_texts():
            text.set_color("black")


@animate_graph(False)
def drift_rate_graph(axes, _):
    """Animate function for the drift rates graph."""
    times, drates, drates_real = __get_drift_rates()
    axes[0].plot(times, drates)
    if len(axes) > 1:
        axes[1].plot(times, drates_real)


def __get_drift_rates():
    times = Graphing.data_coll_cal.times
    drates = Graphing.data_coll_cal.drift_rates
    delta_drates = [dr - drates[0] for dr in drates]
    return times, drates, delta_drates


def formatter(x, _):
    """Format 1 as 1, 0 as 0, and all values whose absolute values is between
    0 and 1 without the leading "0." (e.g., 0.7 is formatted as .7 and -0.4 is
    formatted as -.4)."""
    val_str = '{:g}'.format(x)
    if 0 < np.abs(x) < 1:
        return val_str.replace("0", "", 1)
    else:
        return val_str
