"""
Abstract class defines common functionality between calibration
program and baking program.
"""

# pylint: disable=import-error, relative-import
import sys
import socket
import time
import os
import numpy as np
from tkinter import ttk, messagebox
import queue
import tkinter as tk
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2TkAgg
from matplotlib.figure import Figure

import options_frame
import file_helper as fh
import graphing_helper as gh
import ui_helper

LARGE_FONT = ("Verdana", 13)

BAKING_ID = "Baking"
CAL_ID = "Cal"


class ProgramType(object):  # pylint:disable=too-few-public-methods
    """Defines constants for each type of program."""

    def __init__(self, prog_id):
        self.prog_id = prog_id
        if self.prog_id == BAKING_ID:
            self.title = "Configure Baking"
            self.config_id = fh.BAKING_SECTION
            self.options = options_frame.BAKING
            self.in_prog_msg = "Baking..."
            self.plot_num = 230
            self.num_graphs = 6
        else:
            self.title = "Configure Calibration"
            self.config_id = fh.CAL_SECTION
            self.options = options_frame.CAL
            self.in_prog_msg = "Calibrating..."
            self.plot_num = 240
            self.num_graphs = 7


class Page(ttk.Notebook):  # pylint: disable=too-many-instance-attributes
    """Definition of the abstract program page."""

    def __init__(self, master, id, program_type):
        s = ttk.Style()
        s.configure('InnerNB.TNotebook', tabposition='wn')

        super().__init__(style='InnerNB.TNotebook')  # pylint: disable=missing-super-argument

        self.master = master
        self.id = id
        self.program_type = ProgramType(program_type)
        self.channels = [[], [], [], []]
        self.switches = [[], [], [], []]
        self.snums = []
        self.stable_count = 0
        self.running = False
        self.cancel_run = False
        self.chan_error_been_warned = False
        self.options = None
        self.start_btn = None
        self.data_pts = {}
        
        self.config_frame = ttk.Frame()
        self.graph_frame = ttk.Frame()

        # Need images as instance variables to prevent garbage collection
        self.img_config = tk.PhotoImage(file=r'config.png')
        self.img_graph = tk.PhotoImage(file=r'graph.png')

        # Set up config tab
        self.add(self.config_frame, image=self.img_config)
        self.options = options_frame.OptionsPanel(self.config_frame, self.program_type.options)
        self.start_btn = self.options.create_start_btn(self.start)
        self.options.init_fbgs()
        self.options.pack(expand=True, side="right", fill="both")
        ttk.Button(self.config_frame, text="Delete Tab", command=lambda: master.delete_tab(self.id)).pack()
        
        # Set up graphing tab
        self.add(self.graph_frame, image=self.img_graph)

        # Graphs need to be empty until csv is created
        self.fig = Figure(figsize=(5,5), dpi=100)
        self.main_axes = []
        self.ax_zoom = None
        self.show_main_plots()

        self.canvas = FigureCanvasTkAgg(self.fig, self.graph_frame)
        self.canvas.show()

        self.canvas.get_tk_widget().pack(side=tk.BOTTOM, fill=tk.BOTH, expand=True)
        self.cid = self.canvas.mpl_connect('button_press_event', self.onclick)

        self.toolbar = NavigationToolbar2TkAgg(self.canvas, self.graph_frame)
        self.toolbar.update()
        self.canvas._tkcanvas.pack(side=tk.TOP, fill=tk.BOTH, expand=True) 

        
    def show_main_plots(self):
        # Need to check to make sure Csv is populated, if it is then get axes from graph_helper
        num = self.program_type.plot_num + 1
        #for offs in range(self.program_type.num_graphs):
            #self.main_axes.append(self.fig.add_subplot(num+offs))
        self.main_axes.append(gh.create_mean_wave_time_graph("./output/test0930-2.csv", False, self.fig, num+offs))
        self.main_axes.append(gh.create_wave_power_graph("./output/test0930-2.csv", False, self.fig, num+offs))
        self.main_axes.append(gh.create_temp_time_graph("./output/test0930-2.csv", False, self.fig, num+offs))
        self.main_axes.append(gh.create_mean_power_time_graph("./output/test0930-2.csv", False, self.fig, num+offs))
        self.main_axes.append(gh.create_indiv_waves_graph("./output/test0930-2.csv", False, self.fig, num+offs))
        self.main_axes.append(gh.create_indiv_powers_graph("./output/test0930-2.csv", False, self.fig, num+offs))
        if self.program_type.prog_id == CAL_ID:
            self.main_axes.append(gh.create_drift_rates_graph("./output/test0930-2.csv", False, self.fig, num+offs))

    def graph_back(self, event):
        if event.dblclick:
            self.ax_zoom.cla()
            self.fig.clf()
            self.canvas.draw()
            self.canvas.mpl_disconnect(self.cid)
            self.cid = self.canvas.mpl_connect('button_press_event', self.onclick)
            self.show_main_plots()
            self.canvas.draw()
            self.toolbar.update()

    def onclick(self, event):
        for i, ax in enumerate(self.main_axes):
            if event.dblclick and ax == event.inaxes:
                #print("Click is in axes ax{}".format(i+1))
                for ax in self.main_axes:
                    ax.cla()
                self.fig.clf()
                self.canvas.draw()
                self.toolbar.update()

                self.ax_zoom = self.fig.add_subplot(111)
                self.canvas.mpl_disconnect(self.cid)
                self.cid = self.canvas.mpl_connect('button_press_event', self.graph_back)

                self.ax_zoom.plot(np.random.rand(10))
                self.canvas.draw()
                break
        
    def create_excel(self):
        """Creates excel file."""
        fh.create_excel_file(self.options.file_nme.get())

    def start(self, can_start=False):
        """Starts the recording process."""
        delayed_prog = None

        if False:#not can_start:
            if not self.running:
                conn_fails = []
                if len(sys.argv) > 1 and sys.argv[1] == "-k":
                    self.load_devices(conn_fails)

                for chan, snum, pos in zip(self.options.chan_nums,
                                           self.options.sn_ents,
                                           self.options.switch_positions):
                    if snum.get() != "" and snum.get() not in self.snums:
                        self.snums.append(snum.get())
                        self.channels[chan].append(snum.get())
                        self.switches[chan].append(pos.get())

                if len(conn_fails) == 0:
                    self.running = True
                    self.start_btn.configure(text="Pause")
                    self.header.configure(text=self.program_type.in_prog_msg)
                    ui_helper.lock_widgets(self.options)
                else:
                    conn_str = "Failed to connect to: {}.".format(", ".join(conn_fails))
                    messagebox.showwarning("Device Connection Failure", conn_str)

                delayed_prog = self.master.after(int(self.options.delay.get() *
                                                     1000 * 60 * 60 + .5), lambda: self.start(True))
            else:
                if delayed_prog is not None:
                    self.master.after_cancel(delayed_prog)
                    delayed_prog = None
                self.pause_program()
        else:
            time.sleep(60)
            #self.program_loop()

    def pause_program(self):
        """Pauses the program."""
        self.start_btn.configure(text="Start")
        self.header.configure(text=self.program_type.title)
        ui_helper.unlock_widgets(self.options)
        self.running = False
        self.stable_count = 0
        self.snums = []
        self.channels = [[], [], [], []]
        self.switches = [[], [], [], []]
        if self.oven is not None:
            self.oven.close()
            self.oven = None
        if self.temp_controller is not None:
            self.temp_controller.close()
            self.temp_controller = None
        if self.sm125 is not None:
            self.sm125.close()
            self.sm125 = None
        if self.op_switch is not None:
            self.op_switch.close()
            self.op_switch = None

    def on_closing(self):
        """Stops the user from closing if the program is running."""
        if self.running:
            if messagebox.askyesno("Quit",
                                   "Program is currently running. Are you sure you want to quit?"):
                self.master.destroy()
            else:
                self.master.tkraise()
        else:
            self.master.destroy()
