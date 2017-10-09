"""
Abstract class defines common functionality between calibration
program and baking program.
"""

# pylint: disable=import-error, relative-import
import sys
import socket
from tkinter import ttk, messagebox
import tkinter as tk
import pyvisa as visa
import _thread

import options_frame
import file_helper as fh
import graphing_helper as gh
import ui_helper
import devices

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
        else:
            self.title = "Configre Calibration"
            self.config_id = fh.CAL_SECTION
            self.options = options_frame.CAL
            self.in_prog_msg = "Calibrating..."


class Page(tk.Frame):  # pylint: disable=too-many-instance-attributes
    """Definition of the abstract program page."""
    def __init__(self, parent, master, start_page, program_type):
        super().__init__(parent)  # pylint: disable=missing-super-argument

        self.program_type = program_type
        self.temp_controller = None
        self.oven = None
        self.op_switch = None
        self.sm125 = None
        self.channels = [[], [], [], []]
        self.switches = [[], [], [], []]
        self.snums = []
        self.stable_count = 0
        self.running = False
        self.cancel_run = False
        self.start_page = start_page
        self.chan_error_been_warned = False
        self.options = None
        self.start_btn = None
        self.data_pts = None

        self.main_frame = tk.Frame(self)
        self.header = ttk.Label(self.main_frame, text=self.program_type.title,
                                font=LARGE_FONT)
        self.header.pack(pady=10)
        self.main_frame.pack()
        self.menu = tk.Menu(master, tearoff=0)

    def clear_frame(self):
        """Clears the main frame."""
        self.main_frame.destroy()
        self.main_frame = tk.Frame(self)
        self.main_frame.pack(expand=1, fill=tk.BOTH)

    def home(self, master):
        """Return to StartPage."""
        self.menu = tk.Menu(master, tearoff=0)
        master.config(menu=self.menu)
        master.show_frame(self.start_page, 300, 300)

    def create_menu(self, master):
        """Creates the menu."""
        self.menu.add_command(label="Home", command=lambda: self.home(master))
        self.menu.add_command(label="Create Excel", command=lambda:
                              fh.create_excel_file(
                                  self.options.file_name.get()))
        self.menu.add_command(label="Config",
                              command=lambda: ui_helper.update_config(
                                  self.program_type.config_id))

        graphmenu = tk.Menu(self.menu, tearoff=0)
        animenu = tk.Menu(graphmenu, tearoff=0)
        staticmenu = tk.Menu(graphmenu, tearoff=0)

        menu_items = {"Wavelength v. Time": gh.create_mean_wave_time_graph,
                      "Wavelength v. Power": gh.create_wave_power_graph,
                      "Power v. Time": gh.create_mean_power_time_graph,
                      "Temperature v. Time": gh.create_temp_time_graph,
                      "Indiv. Wavelengths": gh.create_indiv_waves_graph}

        if self.program_type.prog_id == CAL_ID:
            menu_items["Drift Rate"] = gh.create_drift_rates_graph

        for title, func in menu_items:
            self.__create_menu_item(animenu, title, func, True)
            self.__create_menu_item(staticmenu, title, func, False)

        graphmenu.add_cascade(label="Animated", menu=animenu)
        graphmenu.add_cascade(label="Static", menu=staticmenu)
        self.menu.add_cascade(label="Graph", menu=graphmenu)

    def __create_menu_item(self, menu, name, command, is_ani=False):
        fname = self.options.file_name.get()
        menu.add_command(label=name,
                         command=lambda: command(fname, is_ani, True))

    def create_options(self, num_sns):
        """Creates the options panel for the main frame."""
        self.options = options_frame.OptionsPanel(self.main_frame, num_sns,
                                                  self.program_type.options)
        self.start_btn = self.options.create_start_btn(self.start)
        self.options.pack()

    def create_excel(self):
        """Creates excel file."""
        fh.create_excel_file(self.options.file_name.get())

    def load_devices(self, conn_fails):
        """
        Creates the neccessary connections to the devices for the program.
        """
        cont_loc, oven_loc, op_switch_addr, op_switch_port, sm125_addr, \
            sm125_port = fh.get_config(self.config_id)
        manager = visa.ResourceManager()
        if self.options.temp340_state.get():
            try:
                self.temp_controller = devices.TempController(cont_loc, manager)
            except visa.VisaIOError:
                conn_fails.append("LSC 340")
        if self.options.delta_oven_state.get():
            try:
                self.oven = devices.Oven(oven_loc, manager)
                self.oven.set_temp(self.options.baking_temp.get())
                self.oven.heater_on()
            except visa.VisaIOError:
                conn_fails.append("Delta Oven")
        if self.options.op_switch_state.get():
            try:
                self.op_switch = devices.OpSwitch(op_switch_addr, int(op_switch_port))
            except socket.error:
                conn_fails.append("Optical Switch")
        if self.options.sm125_state.get():
            try:
                self.sm125 = devices.SM125(sm125_addr, int(sm125_port))
            except socket.error:
                conn_fails.append("Micron Optics SM125")

    def start(self):
        """Starts the recording process."""
        if not self.running:
            conn_fails = []
            if len(sys.argv) > 1 and sys.argv[1] == "-k":
                self.load_devices(conn_fails)

            for chan, snum, pos in zip(self.options.chan_nums,
                                       self.options.sn_ents,
                                       self.options.switch_positions):
                if snum.get() != "" and snum.get() not in self.snums:
                    self.snums.append(snum.get())
                    self.channels[chan.get() - 1].append(snum.get())
                    self.switches[chan.get() - 1].append(pos.get())

            if len(conn_fails) == 0:
                self.running = True
                self.start_btn.configure(text="Pause")
                self.header.configure(text=self.program_type.in_prog_msg)
                ui_helper.lock_widgets(self.options)
                _thread.start_new_thread(self.program_loop())
            else:
                need_comma = False
                conn_str = "Failed to connect to: "
                for dev in conn_fails:
                    if need_comma:
                        conn_str += ", "
                        need_comma = True
                    conn_str += dev
                conn_str += "."
                messagebox.showwarning("Device Connection Failure", conn_str)

        else:
            self.start_btn.configure(text="Start")
            self.header.configure(text=self.program_type.title)
            ui_helper.unlock_widgets(self.options)
            self.running = False
            self.stable_count = 0
            self.snums = []
            self.channels = [[], [], [], []]
            self.switches = [[], [], [], []]
            self.oven.close()
            self.oven = None
            self.temp_controller.close()
            self.temp_controller = None
            self.sm125.close()
            self.sm125 = None
            self.op_switch.close()
            self.op_switch = None
