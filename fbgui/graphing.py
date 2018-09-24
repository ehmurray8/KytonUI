"""Module used for handling the graphing using matplotlib."""
import gc
import time
import uuid
import threading
import functools
from queue import Queue
from tkinter import StringVar
from typing import Tuple,Callable, Union
import numpy as np
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib import style
from matplotlib.figure import Figure
import matplotlib.ticker as mtick
import matplotlib.animation as animation
import matplotlib.gridspec as gridspec
from matplotlib.axes import Axes
from matplotlib.backend_bases import MouseEvent
from fbgui.graph_toolbar import Toolbar
from fbgui.messages import MessageType, Message
from fbgui.data_container import DataCollection
from fbgui.main_program import Application
from fbgui.config_controller import *
from fbgui.database_controller import DatabaseController

style.use("kyton")


class Graph(object):
    """
    Class describes a specific graph that can be represented as a subplot or a main plot.

    :ivar sub_dims: dimensions for the sub graph, first index of the dims parameter
    :ivar zoom_dims: dimensions for the zoom graph, all dimensions after the first in the dims list parameter
    :ivar sub_axis: Axes object for the sub graph that is plotted in the graph page grid
    :ivar anim: FuncAnimation object when using the animate_func function parameter to animate the graph
    :ivar zoom_axes: list of the axes objects for the zoomed graph
    """

    def __init__(self, title: str, xlabel: str, ylabels: Tuple[str], animate_func: Callable, fig: Figure,
                 dims: List[Union[int, gridspec.GridSpec]], is_cal: bool,
                 snums: List[str], main_queue: Queue, database_controller: DatabaseController):
        """
        Creates a specific graph that represents a sub graph in the graph grid, and the corresponding zoomed
        graph when the graph is double clicked.

        :param title: title of the graph
        :param xlabel: x axis label
        :param ylabels: y axis label, or multiple y axes labels if there are multiple plots in the zoomed graph
        :param animate_func: the function used to animate the graph
        :param fig: matplotlib figure the axes are contained in
        :param dims: the dimensions to use for the axes, first position is the sub graph dimensions, and
                     the remainder of the list is the zoom dimensions
        :param is_cal: True if the program is a calibration program to graph data for, False otherwise
        :param snums: list of serial nums used for the current run that is being graphed
        :param main_queue: queue used for posting logging messages to
        """
        self.title = title
        self.is_cal = is_cal
        self.xlabel = xlabel
        self.ylabels = ylabels
        self.sub_dims = dims[0]
        self.zoom_dims = dims[1:]
        self.main_queue = main_queue
        self.animate_func = animate_func
        self.fig = fig
        self.database_controller = database_controller
        self.sub_axis = None  # type: Axes
        self.anim = None  # type: animation.FuncAnimation
        self.snums = snums
        self.zoom_axes = []  # type: List[Axes]
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

    def check_val_file(self, axes_tuple: Tuple[Axes, ...]):
        """
        Checks whether the currently configured file name is a program stored in the map sql table, and starts
        the animation if it is.

        :param axes_tuple: tuple of matplotlib Axes objects, that will be graphed using the animate function if
                           the program exists
        """
        if self.database_controller.program_exists():
            self.animate_func(axes_tuple, self.snums, self.is_cal)

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
        except IndexError as i:
            self.main_queue.put(Message(MessageType.DEVELOPER, "Main Graph Error Dump", str(i)))


class Graphing(object):
    """
    Class used for graphing the individual Graph objects.

    :cvar data_coll: data collection object for baking graph
    :cvar data_coll_cal: data collection object for the calibration graph

    :ivar graphs: list of Graph objects that are contained in the graphing page
    :ivar sub_axes: List of Axes objects that are plotted on the main graph figure, when showing the graph grid
    """

    data_coll = None  # type: DataCollection
    data_coll_cal = None  # type: DataCollection

    def __init__(self, dims: int, is_cal: bool, figure: Figure,
                 canvas: FigureCanvasTkAgg, toolbar: Toolbar, master: Application,
                 snums: List[str], main_queue: Queue, database_controller: DatabaseController):

        """
        Sets up all of the individual Graph objects for the graphing program page.

        :param fname: tkinter string variable corresponding to the program file name input field
        :param dims: the dimensions for the subplot grid
        :param is_cal: True if the program being graphed is a calibration run, False otherwise
        :param figure: the matplotlib figure of the graphing page
        :param canvas: the matplotlib tkinter canvas containing the figure
        :param toolbar: the matplotlib toolbar object in the canvas
        :param master: the main tkinter application object
        :param snums: list of serial numbers that will be graphed
        :param main_queue: queue used for posting logging messages to
        """
        self.dimensions = dims
        self.is_cal = is_cal
        self.figure = figure
        self.canvas = canvas
        self.toolbar = toolbar
        self.graphs = []  # type: List[Graph]
        self.sub_axes = []  # type: List[Axes]
        self.is_playing = True
        self.master = master
        self.snums = snums
        self.main_queue = main_queue
        self.function_type = CAL if self.is_cal else BAKING
        self.database_controller = database_controller

        threading.Thread(target=self.update_data_coll).start()

        titles = ["Wavelengths vs. Time", "Power vs. Wavelength", "Powers vs. Time", "Temperature vs. Time",
                  "Average {} Power vs. Time".format(u'\u0394'), "Average {} Wavelength vs. Time".format(u'\u0394')]
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

        for i, (title, xlbl, ylbl, anim, dimen) in enumerate(zip(titles, xlabels, ylabels, animate_funcs, dimens)):
            dim_list = [self.dimensions + i + 1]
            for dim in dimen:
                dim_list.append(dim)
            temp = Graph(title, xlbl, ylbl, anim, self.figure, dim_list, self.is_cal, self.snums,
                         self.main_queue, self.database_controller)
            self.graphs.append(temp)
            self.sub_axes.append(temp.sub_axis)
        self.cid = self.canvas.mpl_connect('button_press_event', self.show_main_plot)

        self.canvas.draw()
        self.toolbar.update()

    def update_data_coll(self):
        """Updates the data collections used for graphing the data from the sql table, every 8 seconds."""
        thread_id = uuid.uuid4()
        self.master.thread_map[thread_id] = True
        self.master.graph_threads.append(thread_id)
        while self.master.thread_map[thread_id]:
            try:
                df = self.database_controller.to_data_frame()
                if self.is_cal:
                    Graphing.data_coll_cal = DataCollection()
                    Graphing.data_coll_cal.create(self.is_cal, df)
                else:
                    Graphing.data_coll = DataCollection()
                    Graphing.data_coll.create(self.is_cal, df)
            except RuntimeError as r:
                self.main_queue.put(Message(MessageType.DEVELOPER, "Graphing Update Data Coll Error Dump", str(r)))
            except IndexError as i:
                self.main_queue.put(Message(MessageType.DEVELOPER, "Graphing Update Data Coll Error Dump", str(i)))
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

    def show_subplots(self, event: MouseEvent=None):
        """
        Show all the subplots in the graphing page, when the main plot is double clicked.

        :param event: MouseEvent object passed in on click
        """
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

    def show_main_plot(self, event: Union[MouseEvent, int]):
        """
        Show the main plot, the specified zoomed graph, on the graphing page when double clicked or show
        the graph at the index of event, if event is an integer.

        :param event: MouseEvent corresponding to a click event on the graph, or an integer used to index the graphs
                      list to show that graph
        """
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


def animate_graph(use_snums: bool) -> Callable:
    """
    Animate graph function decorator.

    :param use_snums: If True the function being decorated accepts serial nums as an argument
    """
    def _animate_graph(func: Callable) -> Callable:
        @functools.wraps(func)
        def _wrapper(axes: List[Axes], snums: List[str], is_cal: bool):
            dc = Graphing.data_coll
            if is_cal:
                dc = Graphing.data_coll_cal
            if dc is not None:
                if use_snums:
                    if snums is not None and not len(snums):
                        snums = get_configured_fbg_names(is_cal)
                    func(axes, snums, dc)
                else:
                    func(axes, dc)
        return _wrapper
    return _animate_graph


@animate_graph(False)
def average_wave_graph(axes: List[Axes], dc: DataCollection):
    """
    Animate function for the mean wavelength vs. time graph.

    :param axes: average wavelength Axes as only element
    :param dc: data collection object to use for populating the graph
    """
    times, wavelength_diffs = dc.times, dc.mean_delta_wavelengths_pm
    if len(times) == len(wavelength_diffs):
        axes[0].plot(times, wavelength_diffs)


@animate_graph(True)
def wave_power_graph(axis: List[Axes], snums: List[str], dc: DataCollection):
    """
    Animate function for the wavelength vs. power graph.

    :param axis: wavelength vs power Axes as only element
    :param snums: the serial numbers in use for the corresponding program run being graphed
    :param dc: data collection object to use for populating the graph
    """
    wavelengths, powers = dc.wavelengths, dc.powers
    idx = 0
    axes = []
    for waves, powers, color in zip(wavelengths, powers, HEX_COLORS):
        if len(waves) == len(powers):
            axes.append(axis[0].scatter(waves, powers, color=color, s=75))
        idx += 1

    font_size = 8
    legend = axis[0].legend(axes, snums, bbox_to_anchor=(.5, 1.25), loc='upper center',
                            ncol=int(len(snums) / 2 + 0.5),
                            fontsize=font_size, fancybox=True, shadow=True)
    for text in legend.get_texts():
        text.set_color("black")


@animate_graph(False)
def temp_graph(axes: List[Axes], dc: DataCollection):
    """
    Animate function for the temperature vs. time graph.

    :param axes: delta temperature vs. time Axes, raw temperature vs time Axes
    :param dc: data collection object to use for populating the graph
    """
    times, temp_diffs, temps = dc.times, dc.delta_temps, dc.temps
    if len(times) == len(temp_diffs):
        axes[0].plot(times, temp_diffs)
    if len(axes) > 1 and len(times) == len(temps):
        axes[1].plot(times, temps, color='b')


@animate_graph(False)
def average_power_graph(axis: List[Axes], dc: DataCollection):
    """
    Animate function for the mean power vs. time graph.

    :param axis: average power Axes as only element
    :param dc: data collection object to use for populating the graph
    """
    times, power_diffs = dc.times, dc.mean_delta_powers
    if len(times) == len(power_diffs):
        axis[0].yaxis.set_major_formatter(mtick.FuncFormatter(formatter))
        axis[0].plot(times, power_diffs)


@animate_graph(True)
def wave_graph(axis: List[Axes], snums: List[str], dc: DataCollection):
    """
    Animate function for the individual wavelengths graph.

    :param axis: delat wavelength vs. time Axes, wavelength vs. time Axes
    :param snums: the serial numbers in use for the corresponding program run being graphed
    :param dc: data collection object to use for populating the graph
    """
    times, wavelengths, wavelength_diffs = dc.times, dc.wavelengths, dc.delta_wavelengths_pm
    idx = 0
    axes = []
    for waves, wave_diffs, color in zip(wavelengths, wavelength_diffs, HEX_COLORS):
        if len(times) == len(wave_diffs):
            axes.append(axis[0].plot(times, wave_diffs, color=color)[0])
        if len(axis) > 1 and len(times) == len(waves):
            axis[1].plot(times, waves, color=color)
        idx += 1

    if len(axis) > 1:
        font_size = 8
        legend = axis[0].legend(axes, snums, bbox_to_anchor=(.5, 1.25), loc='upper center',
                                ncol=int(len(snums) / 2 + 0.5), fontsize=font_size, fancybox=True, shadow=True)
        for text in legend.get_texts():
            text.set_color("black")


@animate_graph(True)
def power_graph(axis: List[Axes], snums: List[str], dc: DataCollection):
    """
    Animate function for the individual powers graph.

    :param axis: delta power vs. time Axes, raw power vs. time Axes [Only used for Baking]
    :param snums: the serial numbers in use for the corresponding program run being graphed
    :param dc: data collection object to use for populating the graph
    """
    times, powers, power_diffs = dc.times, dc.powers, dc.delta_powers
    idx = 0
    axes = []
    for pows, pow_diffs, color in zip(powers, power_diffs, HEX_COLORS):
        if len(times) == len(pow_diffs):
            axes.append(axis[0].plot(times, pow_diffs, color=color)[0])
        if len(axis) > 1 and len(times) == len(pows):
            axis[1].plot(times, pows, color=color)
        idx += 1

    if len(axis) > 1:
        font_size = 8
        legend = axis[0].legend(axes, snums, bbox_to_anchor=(.5, 1.25), loc='upper center',
                                ncol=int(len(snums) / 2 + 0.5), fontsize=font_size, fancybox=True, shadow=True)
        for text in legend.get_texts():
            text.set_color("black")


@animate_graph(False)
def drift_rate_graph(axes: List[Axes], dc: DataCollection):
    """
    Animate function for the drift rates graph.

    :param axes: drift rate vs. time Axes, delta drift rate vs. time Axes [Only for Calibration]
    :param dc: data collection object to use for populating the graph
    """
    times, drates, delta_drates = __get_drift_rates(dc)
    if len(times) == len(drates):
        axes[0].plot(times, drates)
    if len(axes) > 1 and len(times) == len(delta_drates):
        axes[1].plot(times, delta_drates)


def __get_drift_rates(dc: DataCollection) -> Tuple[List[float], List[float], List[float]]:
    """
    Get drift rate information about the current calibration run.

    :param dc:
    :return: times, drift rates, delta drift rates for current calibration run
    """
    times = dc.times
    drates = dc.drift_rates
    delta_drates = [dr - drates[0] for dr in drates]
    return times, drates, delta_drates


def formatter(val: float, _):
    """
    Axes label formatter.

    Format 1 as 1, 0 as 0, and all values whose absolute values is between 0 and 1 without the leading "0."
    (e.g., 0.7 is formatted as .7 and -0.4 is formatted as -.4).

    :param val: axis label value
    :param _: not needed
    """
    val_str = '{:g}'.format(val)
    if 0 < np.abs(val) < 1:
        return val_str.replace("0", "", 1)
    else:
        return val_str
