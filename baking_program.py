"""Main entry point for the UI."""
import os.path
import os
import tkinter as tk
import time
import re

import xlsxwriter

import matplotlib
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2TkAgg
from matplotlib.figure import Figure

import controller_340_wrapper as temp_controller
import delta_oven_wrapper as oven_wrapper
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

        #self.controller, self.oven, self.gp700, self.sm125 = init.setup_instruments()

        #Init member vars
        self.sm125_state = tk.IntVar()
        self.gp700_state = tk.IntVar()
        self.delta_oven_state = tk.IntVar()
        self.temp340_state = tk.IntVar()
        self.sn_ents = []

        #Init member widgets
        self.options_grid = tk.Frame(self)
        self.options_grid.pack()

        #Window setup
        master.title("Kyton Baking")
        self.menu = tk.Menu(master, tearoff=0)
        master.config(menu=self.menu)
        self.pack(side="top", fill="both", expand=True)

        self.main_frame = tk.Frame(self)

        self.options = options_panel.OptionsPanel(self.main_frame)
        self.options.create_start_btn(self.start)
        self.options.grid(row=0, column=0, sticky='ew')

        init_time = self.options.init_time.get()
        init_dur = self.options.init_duration.get() * 60
        self.num_stable = int(init_dur/init_time + .5)


        #Wavelength and Power storage
        self.wavelengths = [0]
        self.times = [0]
        self.start_wavelength = 0
        self.start_time = 0

        self.stable_count = 0

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
        if self.options.delta_oven_state.get():
            print("Set oven to " + str(self.options.baking_temp.get()))
            #oven_wrapper.set_temp(self.oven, self.options.baking_temp.get())
        #self.program_loop()

    def check_stable(self):
        """Check if the program is ready to move to primary interval."""
        if self.stable_count < self.num_stable:
            self.stable_count += 1
            return False
        return True

    def program_loop(self):
        """Infinite program loop."""
        if not self.check_stable():
            self.baking_loop()
            self.after(int(self.options.init_time.get()) * 1000, self.program_loop)
            print("init loop")
        else:
            self.baking_loop()
            self.after(int(self.options.prim_time.get()) * 1000 * 60, self.program_loop)
            print("prim loop")

    def baking_loop(self):
        """Runs the baking process."""
        ui_helper.print_options(self.options)

        temperature = temp_controller.get_temp_c(self.controller)
        temperature = float(temperature[:-3])

        amplitudes_avg = []
        wavelengths_avg = []
        count = 0

        need_init = False

        while count < int(self.options.num_pts.get()):
            wavelengths, amplitudes = sm125_wrapper.get_data_actual(self.sm125)
            print("Wavelengths: " + str(wavelengths))
            print("Amplitudes: " + str(amplitudes))

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

        wave_total = 0
        for wavelength in wavelengths_avg:
            wave_total += wavelength
        wave_total /= 4
        if self.start_wavelength == 0:
            self.start_wavelength = wave_total
        else:
            self.wavelengths.append((wave_total - self.start_wavelength) * 10)

        time_total = 0
        for power in amplitudes_avg:
            time_total += power
        time_total /= 4
        if self.start_time == 0:
            self.start_time = time_total
        else:
            self.times.append((time_total - self.start_time) * 10)

        temp2 = temp_controller.get_temp_c(self.controller)
        temperature += float(temp2[:-3])
        temperature /= 2.0

        serial_nums = ["SN#01", "SN#02", "SN#03", "SN#04"]

        i = 0
        while i < 4:
            serial_nums[i] = self.options.sn_ents[i].get()
            i += 1

        write_csv_file(self.options.file_name.get(), serial_nums, \
                    time.time(), temperature,\
                    wavelengths_avg, amplitudes_avg)


def write_csv_file(file_name, serial_nums, timestamp, temp, wavelengths, powers):
    """Write the output csv file."""
    if os.path.isfile(file_name):
        file_obj = open(file_name, "a")
    else:
        file_obj = open(file_name, "w")
        file_obj.write("Serial Num, Timestamp(s), Temperature (C), "\
                + "Wavelength (nm), Power (dBm)\n")
        file_obj.write("----------------------------------------------"\
                +"------------------------\n")

    i = 0
    print(str(serial_nums))
    print(str(wavelengths))
    print(str(powers))
    while i < len(serial_nums):
        file_obj.write(str(serial_nums[i]) + ", " + str(timestamp) + ", " + str(temp) + ", " +\
                    str(wavelengths[i]) + ", " + str(powers[i]) + "\n")
        i += 1

    file_obj.write("\n\n")
    file_obj.close()


def create_excel_file(csv_file):
    """Creates an excel file from the correspoding csv file."""
    xcel_file = csv_file[:-3] + "xlsx"
    if os.path.isfile(xcel_file):
        os.remove(xcel_file)

    if os.path.isfile(csv_file):
        with open(csv_file) as f_obj:
            lines = f_obj.readlines()
            f_obj.close()

        lines = lines[2:]
        words_list = []
        for line in lines:
            words_list.append(line.split(","))

        workbook = xlsxwriter.Workbook(xcel_file)
        worksheet = workbook.add_worksheet()
        worksheet.set_column(0, 4, 18)
        headers = ["Serial Number", "Timestamp (s)", "Temperature (C)", "Wavelength (nm)",\
                    "Power (dBm)"]

        col = 0
        for header in headers:
            worksheet.write(0, col, header)
            col += 1

        row = 1
        for words in words_list:
            col = 0
            for word in words:
                worksheet.write(row, col, word)
                col += 1
            row += 1
        workbook.close()


if __name__ == "__main__":
    ROOT = tk.Tk()
    APP = Application(master=ROOT)
    APP.mainloop()
