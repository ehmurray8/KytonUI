"""Calibratin Program for Kyton UI."""

import sys 
import time 
import tkinter as tk
from tkinter import ttk
from tkinter import messagebox
import _thread
import file_helper
import sm125_wrapper
import ui_helper
import graphing_helper
import pyvisa as visa
import create_options_panel as options_panel
import delta_oven_wrapper as oven_wrapper
import controller_340_wrapper as controller_wrapper
import device_helper

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
        self.chan_error_been_warned = False
        self.finished_point = False
        self.temp_is_good = False

        self.options = None


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

        master.config(menu=self.menu)

        
    def create_options(self, num_sns):
        self.options = options_panel.OptionsPanel(self.main_frame, num_sns, options_panel.CAL)
        self.start_btn = self.options.create_start_btn(self.start)
        self.options.pack()


    def create_excel(self):
        """Creates excel file."""
        file_helper.create_excel_file(self.options.file_name.get())


    def load_devices(self, conn_fails):
        if len(sys.argv) > 1 and sys.argv[1] == "-k":
            resource_manager = visa.ResourceManager()
            cont_loc, oven_loc, gp700_loc, sm125_addr, sm125_port = file_helper.get_config("Calibration")
            if self.options.temp340_state.get():
                try:
                    cont_loc = "GPIB0::{}::INSTR".format(cont_loc)
                    self.controller = resource_manager.open_resource(cont_loc, read_termination=TERM_CHAR)
                except visa.VisaIOError:
                    conn_fails.append("LSC 340")
            if self.options.delta_oven_state.get():
                try:
                    oven_loc = "GPIB0::{}::INSTR".format(oven_loc)
                    self.oven = resource_manager.open_resource(oven_loc, read_termination=TERM_CHAR)
                except visa.VisaIOError:
                    conn_fails.append("Dicon Oven")
            if self.options.gp700_state.get():
                try:
                    gp700_loc = "GPIB0::{}::INSTR".format(gp700_loc)
                    self.gp700 = resource_manager.open_resource(gp700_loc, read_termination=TERM_CHAR)
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
            
            for chan, snum in zip(self.options.chan_nums, self.options.sn_ents):
                if snum.get() != "":
                    self.snums.append(snum.get())
                    self.channels[chan.get() - 1].append(snum.get())

            if len(conn_fails) == 0:
                self.running = True
                self.start_btn.configure(text="Pause")
                self.header.configure(text="Calibrating...")
                ui_helper.lock_widgets(self.options)
                _thread.start_new_thread(lambda: self.run_cal_loop(), ())
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
            self.header.configure(text="Configure Calibration")
            ui_helper.unlock_widgets(self.options)
            self.running = False
            self.cancel_bake = True
            self.stable_count = 0


    def run_cal_loop(self):
        """Runs the calibration."""
        temps_arr = self.options.get_target_temps()

        cycle_num = 0
        while cycle_num < self.options.num_cal_cycles.get():
            for temp in temps_arr:
                print(str(self.oven))
                oven_wrapper.set_temp(self.oven, temp)
                oven_wrapper.heater_on(self.oven)
                oven_wrapper.cooling_off(self.oven)

                start_temp = controller_wrapper.get_temp_k(self.controller)
                
                start_temp = float(start_temp[:-4])

                data_pts, self.chan_error_been_warned = \
                        device_helper.avg_waves_amps(self.sm125, self.channels, self.header, self.options, self.chan_error_been_warned)

                wavelengths_avg = []
                amplitudes_avg = []
                data_pts, self.chan_error_been_warned = \
                          device_helper.avg_waves_amps(self.sm125, self.channels, self.header, self.options, self.chan_error_been_warned)
                for snum in self.snums:
                    wavelengths_avg.append(data_pts[snum][0])
                    amplitudes_avg.append(data_pts[snum][1])

                start_temp += float(controller_wrapper.get_temp_k(self.controller)[:-4])

                start_temp /= 2

                start_time = time.time()

                #Need to write csv file init code
                file_helper.write_csv_file(self.options.file_name.get(), self.snums, start_time, \
                                           start_temp, wavelengths_avg, amplitudes_avg, options_panel.CAL, False, 0.0)

                self.finished_point = False
                self.after(60000, lambda: self.__check_drift_rate(start_time, start_temp))
                while(not self.finished_point):
                    pass

            oven_wrapper.heater_off(self.oven)

            oven_wrapper.set_temp(self.oven, temps_arr[0])

            if self.options.cooling.get():
                oven_wrapper.cooling_on(self.oven)

            _thread.start_new_thread(lambda: self.check_temp(temps_arr), ())
            self.temp_is_good = False
            while(not self.temp_is_good):
                pass

            cycle_num += 1

    def check_temp(self, temps_arr):
        temp = float(controller_wrapper.get_temp_c(self.controller)[:-4])
        while temp > float(temps_arr[0]):
            temp = float(controller_wrapper.get_temp_c(self.controller)[:-4])
        self.temp_is_good = True


    def __check_drift_rate(self, last_time, last_temp):
        curr_temp = float(controller_wrapper.get_temp_k(self.controller)[:-4])

        data_pts, self.chan_error_been_warned = \
                  device_helper.avg_waves_amps(self.sm125, self.channels, self.header, self.options, self.chan_error_been_warned)

        wavelengths_avg = []
        amplitudes_avg = []
        for snum in self.snums:
            wavelengths_avg.append(data_pts[snum][0])
            amplitudes_avg.append(data_pts[snum][1])

        curr_temp += float(controller_wrapper.get_temp_k(self.controller)[:-4])

        curr_temp /= 2

        curr_time = time.time()

        time_diff = float(curr_time - last_time)
        temp_diff = float(curr_temp - last_temp)

        time_ratio_min = curr_time / last_time / 60
        temp_ratio_mk = curr_temp / last_temp / 1000

        drift_rate = temp_ratio_mk / time_ratio_min

        if drift_rate <= self.options.drift_rate.get():
            #record actual point
            file_helper.write_csv_file(self.options.file_name.get(), self.snums, curr_time, \
                                           curr_temp, wavelengths_avg, amplitudes_avg, options_panel.CAL, True, drift_rate)
            self.finished_point = True
        else:
            file_helper.write_csv_file(self.options.file_name.get(), self.snums, curr_time, \
                                           curr_temp, wavelengths_avg, amplitudes_avg, options_panel.CAL, False, drift_rate)
            self.after(60000, lambda: self.__check_drift_rate(curr_time, curr_temp))
