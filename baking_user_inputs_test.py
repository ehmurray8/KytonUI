"""Main entry point for the UI."""
import os.path
import tkinter as tk
import time

#import threading
#import xlsxwriter

import ui_helper
import controller_340_wrapper as temp_controller
import init_instruments as init
import sm125_wrapper
import create_options_panel as options_panel


class Application(tk.Frame):
    """Class containing the main tkinter application."""
    def __init__(self, master):
        """Constructs the app."""
        super().__init__(master)

        self.controller, self.oven, self.gp700, self.sm125 = init.setup_instruments()

        #Init member vars
        self.sm125_state = tk.IntVar()
        self.gp700_state = tk.IntVar()
        self.delta_oven_state = tk.IntVar()
        self.temp340_state = tk.IntVar()
        self.sn_ents = []

        #Init member widgets
        self.options_grid = tk.Frame(self)
        self.options_grid.pack()

        self.baking_temp = tk.DoubleVar()
        self.file_name = tk.StringVar()
        self.sec_time = tk.DoubleVar()
        self.prim_time = tk.DoubleVar()
        self.num_pts = tk.IntVar()

        #Window setup
        master.title("Kyton Baking")
        self.menu = tk.Menu(master, tearoff=0)
        master.config(menu=self.menu)
        self.pack(side="top", fill="both", expand=True)
        options_panel.create_options_grid(self, master)
        ui_helper.create_fibers_sn_grid(self)
        self.create_start_btn()

    def create_start_btn(self):
        """Creates the start button in the app."""
        start_button = tk.Button(self)
        start_button["text"] = "Start"
        start_button["command"] = self.start
        start_button.pack()


    def start(self):
        """Starts the recording process."""
        self.baking_loop()
        #stable = False

        #timer = threading.Timer(int(self.sec_time_entry.get()), self.baking_loop)
        #timer.start()

        #while stable:
        #    i = 0
            #print("Stable")

        #timer.cancel()

        #threading.Timer(int(self.prim_time_entry.get()) * 60,  self.baking_loop()).start()

    def baking_loop(self):
        """Runs the baking process."""
        temperature = temp_controller.get_temp_c(self.controller)
        temperature = float(temperature[:-3])

        amplitudes_avg = []
        wavelengths_avg = []
        count = 0

        need_init = False

        while count < int(self.num_pts.get()):
            wavelengths, amplitudes = sm125_wrapper.get_data_actual(self.sm125)

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

        temp2 = temp_controller.get_temp_c(self.controller)
        temperature += float(temp2[:-3])
        temperature /= 2.0

        serial_nums = ["SN#01", "SN#02", "SN#03", "SN#04", "SN#05", "SN#06", "SN#07",\
                        "SN#08", "SN#09", "SN#10", "SN#11", "SN#12"]

        self.write_csv_file(serial_nums, time.time(), temperature,\
                    wavelengths_avg, amplitudes_avg)


    def write_csv_file(self, serial_nums, timestamp, temp, wavelengths, powers):
        """Write the output csv file."""
        if os.path.isfile(self.file_name.get()):
            file_obj = open(self.file_name.get(), "a")
        else:
            file_obj = open(self.file_name.get(), "w")

        file_obj.write("Serial Num, Timestamp(s), Temperature (C), "\
                + "Wavelength (pm), Power (db)\n")
        file_obj.write("----------------------------------------------"\
                +"------------------------\n")

        i = 0
        while i < len(serial_nums):
            file_obj.write(str(serial_nums[i]) + ": " + str(timestamp) + ", " + str(temp) + ", " +\
                        str(wavelengths[i]) + ", " + str(powers[i]) + "\n")
            i += 1

        file_obj.write("\n\n")
        file_obj.close()



ROOT = tk.Tk()
APP = Application(master=ROOT)
APP.mainloop()
