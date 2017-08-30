"""Main entry point for the UI."""

import time
import sys
import _thread
from tkinter import ttk, messagebox
import tkinter as tk
import pyvisa as visa

import controller_340_wrapper as temp_controller
import delta_oven_wrapper as oven_wrapper
import sm125_wrapper as sm125_wrapper
import create_options_panel as options_panel
import file_helper as file_helper
import graphing_helper as graphing_helper
import ui_helper as ui_helper


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

        self.main_frame.pack()      

        self.stable_count = 0

        self.menu = tk.Menu(master, tearoff=0)

        self.running = False
        self.cancel_bake = False
        self.start_page = start_page
        self.chan_error_been_warned = False

        self.options = None
        self.start_btn = None


    def clear_frame(self):
        """Clears the main frame."""
        self.main_frame.destroy()
        self.main_frame = tk.Frame(self)
        self.main_frame.pack(expand=1, fill=tk.BOTH)


    def home(self, master):
        """Returns the program to the main page."""
        self.menu = tk.Menu(master, tearoff=0)
        master.config(menu=self.menu)
        master.show_frame(self.start_page, 300, 300)


    def create_menu(self, master):
        """Creates the baking menu."""
        self.menu.add_command(label="Home", command=lambda: self.home(master))
        self.menu.add_command(label="Create Excel", command=lambda: \
                file_helper.create_excel_file(self.options.file_name.get()))
        self.menu.add_command(label="Config", command=lambda: ui_helper.update_config("Baking"))

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
        """Creates the options panel for the main frame."""
        self.options = options_panel.OptionsPanel(self.main_frame, num_sns, options_panel.BAKING)
        self.start_btn = self.options.create_start_btn(self.start)
        self.options.pack()


    def create_excel(self):
        """Creates excel file."""
        file_helper.create_excel_file(self.options.file_name.get())


    def load_devices(self, conn_fails):
        """Creates the neccessary connections to the devices for the program."""
        cont_loc, oven_loc, gp700_loc, sm125_addr, sm125_port = \
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
            except visa.VisaIOError:
                conn_fails.append("Delta Oven")
        if self.options.gp700_state.get():
            gp700_loc = "GPIB0::{}::INSTR".format(gp700_loc)
            try:
                self.gp700 = resource_manager \
                        .open_resource(gp700_loc, read_termination=TERM_CHAR)
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
                self.header.configure(text="Baking...")
                self.program_loop()
            else:
                need_comma = False
                conn_str = "Failed to connect to: "
                for dev in conn_fails:
                    if need_comma:
                        conn_str += ", "
                    conn_str += dev
                    need_comma = True
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
        #pylint:disable=too-many-locals, too-many-branches, too-many-statements
        amplitudes_avg = []
        wavelengths_avg = []
        count = 0
        need_init = True
        while count < int(self.options.num_pts.get()):
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

            if need_init:
                wavelengths_avg = [0] * len(wavelengths[0])
                amplitudes_avg = [0] * len(amplitudes[0])
                need_init = False
                i = 0

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
        chan_errs = []
        for chan in self.channels:
            max_pts = lens[chan_num-1]
            temp = chan_num
            start_index = 0
            while temp > 1:
                start_index += lens[temp-2]
                temp -= 1
            count = 0
            for snum in chan:
                if count < max_pts:
                    data_pts[snum] = (wavelengths_avg[start_index],
                                      amplitudes_avg[start_index])
                    start_index += 1
                else:
                    chan_errs.append(snum)
                    data_pts[snum] = (0, 0)
                count += 1
            chan_num += 1

        if len(chan_errs) > 0:
            self.chan_error(chan_errs)
        return data_pts


    def chan_error(self, snums):
        """Creates the error messsage to alert the user not enough fbgs are being scanned."""
        if not self.chan_error_been_warned:
            self.chan_error_been_warned = True
            errs_str = "Micron Optics didn't report any data for the serial numbers: "
            need_comma = False
            for snum in snums:
                if need_comma:
                    errs_str += ", "
                errs_str += str(snum)
                need_comma = True

            #TODO make this threaded
            # _thread.start_new_thread(lambda: tk.messagebox.showwarning("Scanning error", errs_str))
            tk.messagebox.showwarning("Scanning error", errs_str)


    def baking_loop(self):
        """Runs the baking process."""
        #print("Started baking loop...")

        if len(sys.argv) > 1 and sys.argv[1] == "-k":
            temperature = temp_controller.get_temp_c(self.controller)
            temperature = float(temperature[:-3])
        else:
            temperature = 0.0

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
