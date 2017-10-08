import time
import sys
from tkinter import ttk, messagebox
import tkinter as tk
import pyvisa as visa

import controller_340_wrapper as temp_controller
import delta_oven_wrapper as oven_wrapper
import sm125_wrapper as sm125_wrapper
import create_options_panel as options_panel
import file_helper as file_helper
import graphing_helper as graphing_helper
import ui_helper
import device_helper
import optical_switch_wrapper as op_switch_wrapper


TERM_CHAR = '/n'
LARGE_FONT = ("Verdana", 13)

BAKING_ID = "Baking"
CAL_ID  = "Cal"

class ProgramType():
    def __init__(self, prog_id):
        if prog_id == BAKING_ID:
            self.title = "Configure Baking"
            self.config_id = file_helper.BAKING_SECTION
            self.options = options_panel.BAKING
            self.in_prog_msg = "Baking..."
        else:
            self.title = "Configre Calibration"
            self.config_id = file_helper.CAL_SECTION
            self.options = options_panel.CAL
            self.in_prog_msg = "Calibrating..."


class Page(tk.Frame):
    def __init__(self, parent, master, start_page, program_type):
        """Constructs the app."""
        super().__init__(parent)

        self.program_type = program_type

        self.controller = None
        self.oven = None
        self.op_switch = None
        self.sm125 = None
        self.channels = [[], [], [], []]
        self.switches = [[], [], [], []]
        self.snums = []

        self.main_frame = tk.Frame(self)

        self.header = ttk.Label(self.main_frame, text=self.program_type.title, font=LARGE_FONT)
        self.header.pack(pady=10)

        self.main_frame.pack()      

        self.stable_count = 0

        self.menu = tk.Menu(master, tearoff=0)

        self.running = False
        self.cancel_run = False
        self.start_page = start_page
        self.chan_error_been_warned = False

        self.options = None
        self.start_btn = None
        self.data_pts = None


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
        self.menu.add_command(label="Home", command=lambda: self.home(master))
        self.menu.add_command(label="Create Excel", command=lambda: \
                file_helper.create_excel_file(self.options.file_name.get()))
        self.menu.add_command(label="Config", command=lambda: ui_helper.update_config(self.program_type.config_id))

        graphmenu = tk.Menu(self.menu, tearoff=0)
        animenu = tk.Menu(graphmenu, tearoff=0)
        staticmenu = tk.Menu(graphmenu, tearoff=0)
        animenu.add_command(label="Wavelength v. Time", command=lambda: \
                graphing_helper.create_mean_wave_time_graph(self.options.file_name.get(), True, True))
        animenu.add_command(label="Wavelength v. Power", command=lambda: \
                graphing_helper.create_wave_power_graph(self.options.file_name.get(), True, True))
        animenu.add_command(label="Power v. Time", command=lambda: \
                graphing_helper.create_mean_power_time_graph(self.options.file_name.get(), True, True))
        animenu.add_command(label="Temperature v. Time", command=lambda: \
                graphing_helper.create_temp_time_graph(self.options.file_name.get(), True, True))
        animenu.add_command(label="Indiv. Wavelengths", command=lambda: \
                graphing_helper.create_indiv_waves_graph(self.options.file_name.get(), True, True))
        animenu.add_command(label="Indiv. Powers", command=lambda: \
                graphing_helper.create_indiv_powers_graph(self.options.file_name.get(), True, True))
        animenu.add_command(label="Drift Rate", command=lambda: \
                graphing_helper.create_drift_rates_graph(self.options.file_name.get(), True, True))


        staticmenu.add_command(label="Wavelength v. Time", command=lambda: \
                graphing_helper.create_mean_wave_time_graph(self.options.file_name.get(), False, True))
        staticmenu.add_command(label="Wavelength v. Power", command=lambda: \
                graphing_helper.create_wave_power_graph(self.options.file_name.get(), False, True))
        staticmenu.add_command(label="Power v. Time", command=lambda: \
                graphing_helper.create_mean_power_time_graph(self.options.file_name.get(), False, True))
        staticmenu.add_command(label="Temperature v. Time", command=lambda: \
                graphing_helper.create_temp_time_graph(self.options.file_name.get(), False, True))
        staticmenu.add_command(label="Indiv. Wavelengths", command=lambda: \
                graphing_helper.create_indiv_waves_graph(self.options.file_name.get(), False, True))
        staticmenu.add_command(label="Indiv. Powers", command=lambda: \
                graphing_helper.create_indiv_powers_graph(self.options.file_name.get(), False, True))
        staticmenu.add_command(label="Drift Rate", command=lambda: \
                graping_helper.create_drift_rates_graph(self.options.file_name.get(), False, True))


        graphmenu.add_cascade(label="Animated", menu=animenu)
        graphmenu.add_cascade(label="Static", menu=staticmenu)
        self.menu.add_cascade(label="Graph", menu=graphmenu)

    def create_options(self, num_sns):
        """Creates the options panel for the main frame."""
        self.options = options_panel.OptionsPanel(self.main_frame, num_sns, self.program_type.options)
        self.start_btn = self.options.create_start_btn(self.start)
        self.options.pack()

    def create_excel(self):
        """Creates excel file."""
        file_helper.create_excel_file(self.options.file_name.get())

    def load_devices(self, conn_fails):
        """Creates the neccessary connections to the devices for the program."""
        cont_loc, oven_loc, op_switch_addr, op_switch_port, sm125_addr, sm125_port = \
                        file_helper.get_config("Baking")
        resource_manager = visa.ResourceManager()
        if self.options.temp340_state.get():    
            try:
                cont_loc = "GPIB0::{}::INSTR".format(cont_loc)
                self.controller = \
                    resource_manager.open_resource(cont_loc, read_termination=TERM_CHAR)
            except visa.VisaIOError:
                conn_fails.append("LSC 340")
        if self.options.delta_oven_state.get():
            try:
                oven_loc = "GPIB0::{}::INSTR".format(oven_loc)
                self.oven = \
                        resource_manager.open_resource(oven_loc, read_termination=TERM_CHAR)
                oven_wrapper.set_temp(self.oven, self.options.baking_temp.get())
                oven_wrapper.heater_on(self.oven)
            except visa.VisaIOError:
                conn_fails.append("Delta Oven")
        if self.options.op_switch_state.get():
            try:
                self.op_switch = op_switch_wrapper.setup(op_switch_addr, int(op_switch_port))
            except visa.VisaIOError:
                conn_fails.append("Optical Switch")
        if self.options.sm125_state.get():
            try:
                self.sm125 = sm125_wrapper.setup(sm125_addr, int(sm125_port))
            except visa.VisaIOError:
                conn_fails.append("Micron Optics SM125")


    def start(self):
        """Starts the recording process."""
        if not self.running:
            conn_fails = []
            if len(sys.argv) > 1 and sys.argv[1] == "-k":
                self.load_devices(conn_fails)

            for chan, snum, pos in zip(self.options.chan_nums, self.options.sn_ents, self.options.switch_positions):
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
            self.controller.close()
            self.controller = None
            self.sm125.close()
            self.sm125 = None
            self.op_switch.close()
            self.op_switch = None


