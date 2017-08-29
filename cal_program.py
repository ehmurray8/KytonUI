"""Calibratin Program for Kyton UI."""

import sys
import tkinter as tk
from tkinter import ttk
from tkinter import messagebox
import file_helper
import sm125_wrapper
import ui_helper
import graphing_helper
import pyvisa as visa
import create_options_panel as options_panel

LARGE_FONT = ("Verdana", 13)
TERM_CHAR = "\n"

class CalPage(tk.Frame): # pylint: disable=too-many-ancestors, too-many-instance-attributes
    """Class containing the main tkinter application."""

    def __init__(self, parent, master, start_page):
        """Constructs the app."""
        tk.Frame.__init__(self, parent)

        self.controller = None
        self.oven = None
        self.gp700 = None
        self.sm125 = None
        self.channels = [[], [], [], []]
        self.switches = []
        self.snums = []

        self.main_frame = tk.Frame(self)

        self.header = ttk.Label(self.main_frame, text="Configure Calibration", font=LARGE_FONT)
        self.header.pack(pady=10)

        self.stable_count = 0

        self.menu = tk.Menu(master, tearoff=0)

        self.running = False
        self.cancel_bake = False
        self.start_page = start_page


    def clear_frame(self):
        """Clear the main frame, and construct a new blank main frame."""
        self.main_frame.destroy()
        self.main_frame = tk.Frame(self)
        self.main_frame.pack(expand=1, fill=tk.BOTH)


    def home(self, master):
        """Return to StartPage."""
        self.menu = tk.Menu(master, tearoff=0)
        master.config(menu=self.menu)
        master.show_frame(self.start_page, 300, 300)


    def create_menu(self, master):
        self.menu.add_command(label="Home", command=lambda: self.home(master))
        self.menu.add_command(label="Create Excel", command=lambda: \
                file_helper.create_excel_file(self.options.file_name.get()))
        self.menu.add_command(label="Config", command=lambda: ui_helper.update_config("Calibration"))

        graphmenu = tk.Menu(self.menu, tearoff=0)
        animenu = tk.Menu(graphmenu, tearoff=0)
        staticmenu = tk.Menu(graphmenu, tearoff=0)
        animenu.add_command(label="Wavelength v. Time", command=lambda: \
                graphing_helper.create_mean_wave_time_graph(self.options.file_name.get(), True))
        animenu.add_command(label="Wavelength v. Power", command=lambda: \
                graphing_helper.create_wave_power_graph(self.options.file_name.get(), True))
        animenu.add_command(label="Power v. Time", command=lambda: \
                graphing_helper.create_mean_power_time_graph(self.options.file_name.get(), True))
        animenu.add_command(label="Temperature v. Time", command=lambda: \
                graphing_helper.create_temp_time_graph(self.options.file_name.get(), True))
        animenu.add_command(label="Indiv. Wavelengths", command=lambda: \
                graphing_helper.create_indiv_waves_graph(self.options.file_name.get(), True))
        animenu.add_command(label="Indiv. Powers", command=lambda: \
                graphing_helper.create_indiv_powers_graph(self.options.file_name.get(), True))


        staticmenu.add_command(label="Wavelength v. Time", command=lambda: \
                graphing_helper.create_mean_wave_time_graph(self.options.file_name.get(), False))
        staticmenu.add_command(label="Wavelength v. Power", command=lambda: \
                graphing_helper.create_wave_power_graph(self.options.file_name.get(), False))
        staticmenu.add_command(label="Power v. Time", command=lambda: \
                graphing_helper.create_mean_power_time_graph(self.options.file_name.get(), False))
        staticmenu.add_command(label="Temperature v. Time", command=lambda: \
                graphing_helper.create_temp_time_graph(self.options.file_name.get(), False))
        staticmenu.add_command(label="Indiv. Wavelengths", command=lambda: \
                graphing_helper.create_indiv_waves_graph(self.options.file_name.get(), False))
        staticmenu.add_command(label="Indiv. Powers", command=lambda: \
                graphing_helper.create_indiv_powers_graph(self.options.file_name.get(), False))


        graphmenu.add_cascade(label="Animated", menu=animenu)
        graphmenu.add_cascade(label="Static", menu=staticmenu)
        self.menu.add_cascade(label="Graph", menu=graphmenu)

        master.config(menu=self.menu)

        
    def create_options(self, num_sns):
        self.options = options_panel.OptionsPanel(self.main_frame, num_sns, options_panel.CAL)
        self.start_btn = self.options.create_start_btn(self.start)
        self.options.pack()


    def create_excel(self):
        """Creates excel file."""
        file_helper.create_excel_file(self.options.file_name.get())

    
    def start(self):
        """Starts the recording process."""
        if not self.running:
            
            conn_fails = []
            if len(sys.argv) > 1 and sys.argv[1] == "-k":
                resource_manager = visa.ResourceManager()
                cont_loc, oven_loc, gp700_loc, sm125_addr, sm125_port = file_helper.get_config("Calibration")
                if self.options.temp340_state.get():
                    try:
                        self.controller = resource_manager.open_resource(cont_loc, read_termination=TERM_CHAR)
                    except visa.VisaIOError:
                        conn_fails.append("LSC 340")
                if self.options.delta_oven_state.get():
                    try:
                        self.oven = resource_manager.open_resource(oven_loc, read_termination=TERM_CHAR)
                    except visa.VisaIOError:
                        conn_fails.append("Dicon Oven")
                if self.options.gp700_state.get():
                    try:
                        self.gp700 = resource_manager.open_resource(gp700_loc, read_termination=TERM_CHAR)
                    except visa.VisaIOError:
                        conn_fails.append("Optical Switch")
                if self.options.sm125_state.get():
                    try:
                        self.sm125 = sm125_wrapper.setup(sm125_addr, int(sm125_port))
                    except visa.VisaIOError:
                        conn_fails.append("Micron Optics SM125")

            for chan, snum in zip(self.options.chan_nums, self.options.sn_ents):
                if snum.get() != "":
                    self.snums.append(snum.get())
                    self.channels[chan.get() - 1].append(snum.get())

            if len(conn_fails) == 0:
                self.running = True
                self.start_btn.configure(text="Pause")
                self.header.configure(text="Calibrating...")
            else:
                need_comma = False
                conn_str = "Failed to connect to: "
                for dev in conn_fails:
                    if need_comma:
                        conn_str += ", "
                    conn_str += dev
                conn_str += "."
                messagebox.showwarning("Device Connection Failure", conn_str)

        else:
            self.start_btn.configure(text="Start")
            self.header.configure(text="Configure Calibration")
            self.running = False
            self.cancel_bake = True
            self.stable_count = 0

