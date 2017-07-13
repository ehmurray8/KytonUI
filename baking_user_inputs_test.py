"""Main entry point for the UI."""
import os.path
import tkinter as tk
import time

#import threading
#import xlsxwriter

import matplotlib
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2TkAgg
from matplotlib.figure import Figure

import controller_340_wrapper as temp_controller
import init_instruments as init
import sm125_wrapper
import create_options_panel as options_panel
import ui_helper

from numpy import arange, sin, pi

matplotlib.use('TkAgg')


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

        self.main_frame = tk.Frame(self)

        self.options = options_panel.OptionsPanel(self.main_frame)
        self.options.create_start_btn(self.start)
        self.options.grid(row=0, column=0, sticky='ew')

        self.create_graph()
        self.main_frame.pack(expand=1, fill=tk.BOTH)


    def create_graph(self):
        """Creates the graph."""
        fig = Figure(figsize=(5, 4), dpi=100)
        sub = fig.add_subplot(111)
        rng = arange(0.0, 3.0, 0.01)
        y_vals = sin(2*pi*rng)

        sub.plot(rng, y_vals)


        # a tk.DrawingArea
        canvas = FigureCanvasTkAgg(fig, self.main_frame)
        canvas.show()
        canvas.get_tk_widget().grid(row=0, column=1)

        toolbar = NavigationToolbar2TkAgg(canvas, ROOT)
        toolbar.update()


    def start(self):
        """Starts the recording process."""
        self.baking_loop()
        #ui_helper.print_options(self.options)
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

        write_csv_file(self.options.file_name.get(), serial_nums, \
                    time.time(), temperature,\
                    wavelengths_avg, amplitudes_avg)


def write_csv_file(file_name, serial_nums, timestamp, temp, wavelengths, powers):
    """Write the output csv file."""
    if os.path.isfile(file_name.get()):
        file_obj = open(file_name.get(), "a")
    else:
        file_obj = open(file_name.get(), "w")

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
