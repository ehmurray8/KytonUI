#pylint:disable=unused-import, wrong-import-position
"""Main entry point for the UI."""
import tkinter as tk
from tkinter import ttk
from tkinter import messagebox
from tkinter import font
import time
import sys
import pyvisa as visa

import controller_340_wrapper as temp_controller
import delta_oven_wrapper as oven_wrapper
import sm125_wrapper
import create_options_panel as options_panel
import file_helper
import graphing_helper
import ui_helper 
from main_program import *


NUM_SNS = 4
TERM_CHAR = '/n'

LARGE_FONT = ("Verdana", 13)

class BakingPage(tk.Frame): # pylint: disable=too-many-ancestors, too-many-instance-attributes
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

        self.header = ttk.Label(self.main_frame, text="Configure Baking", font=LARGE_FONT)
        self.header.pack(pady=10)
        
        self.stable_count = 0

        self.menu = tk.Menu(master, tearoff=0)

        self.running = False
        self.cancel_bake = False
        self.start_page = start_page


    def clear_frame(self):
        self.main_frame.destroy()
        self.main_frame = tk.Frame(self)
        self.main_frame.pack(expand=1, fill=tk.BOTH)

    def home(self, master):
        self.menu = tk.Menu(master, tearoff=0)
        master.config(menu=self.menu)
        master.show_frame(self.start_page, 300, 300)


    def create_menu(self, master):
        self.menu.add_command(label="Home", command=lambda: self.home(master))
        self.menu.add_command(label="Create Excel", command=lambda: \
                file_helper.create_excel_file(self.options.file_name.get()))
        self.menu.add_command(label="Config", command=update_config)

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
        self.options = options_panel.OptionsPanel(self.main_frame, num_sns)
        self.start_btn = self.options.create_start_btn(self.start)
        #self.options.grid(row=0, column=0, sticky='ew')
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
                if self.options.temp340_state.get():
                    controller_location = "GPIB0::{}::INSTR".format(CPARSER.get("Calibration",
                                                                    "controller_location"))
                    try:
                        self.controller = resource_manager.open_resource(controller_location,
                            read_termination=TERM_CHAR)
                    except visa.VisaIOError:
                        conn_fails.append("LSC 340")
                if self.options.delta_oven_state.get():
                    oven_location = "GPIB0::{}::INSTR".format(CPARSER.get("Calibration",
                                                            "oven_location"))
                    self.oven = resource_manager.open_resource(oven_location,
                            read_termination=TERM_CHAR)
                    try:
                        oven_wrapper.set_temp(self.oven, self.options.baking_temp.get())
                    except visa.VisaIOError:
                        conn_fails.append("Dicon Oven")
                if self.options.gp700_state.get():
                    gp700_location = "GPIB0::{}::INSTR".format(CPARSER.get("Calibration",
                                                            "gp700_location"))
                    try:
                        self.gp700 = resource_manager.open_resource(gp700_location,
                            read_termination=TERM_CHAR)
                    except visa.VisaIOError:
                        conn_fails.append("Optical Switch")
                if self.options.sm125_state.get():
                    sm125_address =CPARSER.get("Calibration", "sm125_address")
                    sm125_port = CPARSER.get("Calibration", "sm125_port")
                    try:
                        self.sm125 = sm125_wrapper.setup(sm125_address, int(sm125_port))
                    except visa.VisaIOError:
                        conn_fails.append("Micron Optics SM125")

            for chan, snum in zip(self.options.chan_nums, self.options.sn_ents):
                if snum.get() != "":
                    self.snums.append(snum.get())
                    self.channels[chan.get() - 1].append(snum.get())

            if len(conn_fails) == 0:
                self.running = True
                self.start_btn.configure(text="Pause")
                self.header.configure(text="Baking...")
                self.program_loop()
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
            self.header.configure(text="Configure Baking")
            self.running = False
            self.cancel_bake = True
            self.stable_count = 0

    def check_stable(self):
        """Check if the program is ready to move to primary interval."""
        init_time = self.options.init_time.get()
        init_dur = self.options.init_duration.get() * 60
        num_stable = int(init_dur/init_time + .5)

        if self.stable_count < num_stable:
            self.stable_count += 1
            return False
        return True

    def program_loop(self):
        """Infinite program loop."""
        #print("Started program loop...")
        if not self.cancel_bake:
            if not self.check_stable():
                self.baking_loop()
                self.after(int(self.options.init_time.get()) * 1000, self.program_loop)
            else:
                self.baking_loop()
                self.after(int(self.options.prim_time.get()) * 1000 * 60, self.program_loop)

    def __avg_waves_amps(self):
        #pylint:disable=too-many-locals, too-many-branches
        amplitudes_avg = []
        wavelengths_avg = []
        count = 0
        need_init = False
        while count < int(self.options.num_pts.get()):
            #wavelengths, amplitudes = sm125_wrapper.get_data_channels(self.options.chan_nums)
            #TODO Need to associate proper amplitudes/powers with correct serial number
            #
            if len(sys.argv) > 1 and sys.argv[1] == "-k":
                can_connect = False

                while not can_connect:
                    try:
                        wavelengths, amplitudes, lens = sm125_wrapper.get_data_actual(self.sm125)
                        can_connect = True
                    except visa.VisaIOError:
                        self.header.configure(text="SM125 Connection Error...Trying Again")
                self.header.configure(text="Baking...")
            else:
                wavelengths = [[]]
                amplitudes = [[]]
                lens = [0, 0, 0, 0]

            #TODO make sure wavelengths and amplitudes are 2d lists with one list per channel
            enough_readings = False
            for length, wavelens in zip(lens, wavelengths):
                if len(wavelens) > length:
                    #Curr channel more wavelengths are expected than received
                    pass
                else:
                    enough_readings = True

            if not need_init:
                wavelengths_avg = [0] * len(wavelengths[0])
                amplitudes_avg = [0] * len(amplitudes[0])
                need_init = True

            i = 0
            for wavelength_list in wavelengths:
                for wavelength in wavelength_list:
                    wavelengths_avg[i] += wavelength
                    i += 1

            i = 0
            for ampl in amplitudes:
                for amp in ampl:
                    amplitudes_avg[i] += amp
                    i += 1

            count += 1

        i = 0
        while i < len(wavelengths_avg):
            wavelengths_avg[i] /= (count)
            amplitudes_avg[i] /= (count)
            i += 1

        chan_num = 1
        data_pts = {}
        #print(str(self.channels))
        for chan in self.channels:
            max_pts = lens[chan_num-1]
            temp = chan_num
            start_index = 0
            while temp > 1:
                start_index += lens[temp-2]
                temp -= 1
            count = 0
            #print(str(chan))
            for snum in chan:
                if count < max_pts:
                    data_pts[snum] = (wavelengths_avg[start_index],
                                           amplitudes_avg[start_index])
                    start_index += 1
                else:
                    data_pts[snum] = (None, None)
                count += 1
            chan_num += 1

        return data_pts
        #return wavelengths_avg, amplitudes_avg


    def baking_loop(self):
        """Runs the baking process."""
        #print("Started baking loop...")

        if len(sys.argv) > 1 and sys.argv[1] == "-k":
            temperature = temp_controller.get_temp_c(self.controller)
            temperature = float(temperature[:-3])
        else:
            temperature = 0

        #wavelengths_avg, amplitudes_avg = self.__avg_waves_amps()
        wavelengths_avg = []
        amplitudes_avg = []
        data_pts = self.__avg_waves_amps()
        for snum in self.snums:#self.options.sn_ents:
            wavelengths_avg.append(data_pts[snum][0])
            amplitudes_avg.append(data_pts[snum][1])


        if len(sys.argv) > 1 and sys.argv[1] == "-k":
            temp2 = temp_controller.get_temp_c(self.controller)
            temperature += float(temp2[:-3])

        temperature /= 2.0

        #serial_nums = []
        #for sn_ent in self.options.sn_ents:
        #    serial_nums.append(sn_ent.get())

        curr_time = time.time()

        if len(sys.argv) > 1 and sys.argv[1] == "-k":
            file_helper.write_csv_file(self.options.file_name.get(), self.snums,
                    curr_time, temperature, wavelengths_avg, amplitudes_avg)


def update_config():
    """Updates devices configuration."""
    cont_loc = CPARSER.get("Devices", "controller_location")
    oven_loc = CPARSER.get("Devices", "oven_location")
    gp700_loc = CPARSER.get("Devices", "gp700_location")
    sm125_addr = CPARSER.get("Devices", "sm125_address")
    sm125_port = CPARSER.get("Devices", "sm125_port")

    old_conf = [cont_loc, oven_loc, gp700_loc, sm125_addr, sm125_port]

    popup = tk.Toplevel()
    popup.wm_title("Device Configuration")
    frame = tk.Frame(popup)
    frame.pack()
    config_grid = tk.Frame(frame)
    config_grid.pack(side="top", fill="both", expand=True, padx=10)

    ttk.Label(config_grid, text="340 Controller GPIB0 Port:").grid(row=0, padx=5)
    cont_ent = ttk.Entry(config_grid)
    cont_ent.grid(row=0, column=1, padx=5)
    cont_ent.insert(0, str(cont_loc))

    ttk.Label(config_grid, text="Dicon Oven GPIB0 Port:").grid(row=1, padx=5)
    oven_ent = ttk.Entry(config_grid)
    oven_ent.grid(row=1, column=1, padx=5)
    oven_ent.insert(0, str(oven_loc))

    ttk.Label(config_grid, text="GP700 Switch GPIB0 Port:").grid(row=2, padx=5)
    gp700_ent = ttk.Entry(config_grid)
    gp700_ent.grid(row=2, column=1, padx=5)
    gp700_ent.insert(0, str(gp700_loc))

    ttk.Label(config_grid, text="SM125 IP Address:").grid(row=3, padx=5)
    sm125_addr_ent = ttk.Entry(config_grid)
    sm125_addr_ent.grid(row=3, column=1, padx=5)
    sm125_addr_ent.insert(0, str(sm125_addr))

    ttk.Label(config_grid, text="SM125 IP Port:").grid(row=4, padx=5)
    sm125_port_ent = ttk.Entry(config_grid)
    sm125_port_ent.grid(row=4, column=1, padx=5)
    sm125_port_ent.insert(0, str(sm125_port))


    conf_widgets = [cont_ent, oven_ent, gp700_ent, sm125_addr_ent, sm125_port_ent]

    ttk.Button(frame, text="Save", command=lambda: file_helper.save_config(cont_ent, oven_ent, \
            gp700_ent, sm125_addr_ent, sm125_port_ent, popup)). \
            pack(side="top", fill="both", expand=True, pady=10)

    ui_helper.open_center(350, 150, popup)
    popup.protocol("WM_DELETE_WINDOW", lambda: file_helper.on_closing(popup, old_conf, conf_widgets))


if __name__ == "__main__":
    ROOT = None
    launch()
