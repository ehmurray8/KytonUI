import os.path
import tkinter as tk
import threading

import xlsxwriter

import create_options_panel as options_panel
import controller_340_wrapper as temp_controller
import init_instruments as init
import sm125_wrapper


class Application(tk.Frame):
    def __init__(self, master):
        super().__init__(master)

        self.controller, self.oven, self.gp700, self.sm125 = init.setup_instruments()
        options_panel.create_options_grid(self, master)


    def start(self):
        stable = False

        timer = threading.Timer(self.sec_time_entry.get(), self.baking_loop)
        timer.start()

        while stable:
            print("Stable")

        timer.cancel()

        threading.Timer(self.prim_time_entry.get() * 60,  self.baking_loop()).start()

    def baking_loop(self):
        temperature = temp_controller.get_temp_c(self.oven)
        amplitudes_avg = []
        wavelengths_avg = []
        count = 0
        while (count < self.num_pts_entry.get()):
            wavelengths, amplitudes, timestamp = sm125_wrapper.get_data_built_in(self.sm125)
            i = 0
            for wl in wavelengths:
                wavelengths_avg[i] += wl
                i += 1

            i = 0
            for amp in amplitudes:
                amplitudes_avg[i] += amp
                i += 1

            count += 1

        temperature += temp_controller.get_temp_c(self.oven)
        temperature /= 2

    def write_csv_file(self, serial_num, temp, wavelength, amplitude):
        if os.path.isfile(self.file_entry.get()):
            file_obj = open(self.file_entry.get() + "_" + serial_num + ".csv", "a")
        else:
            file_obj = open(self.file_entry.get() + "_" + serial_num + ".csv", "w")
            file_obj.write(serial_num)
            file_obj.write("Temperature (C), Wavelength (pm), Power (db)")

        file_obj.write(temp + ", " + wavelength + ", " + amplitude)
        file_obj.close()

    def print_options(self):
        print("SM125: " + format_selected(self.sm125_state.get()))
        print("GP700: " + format_selected(self.gp700_state.get()))
        print("Temp340: " + format_selected(self.temp340_state.get()))
        print("Delta Oven: " + format_selected(self.delta_oven_state.get()))
        print("Points to average: " + self.num_pts_entry.get())
        print("Primary time interval: " + self.prim_time_entry.get())
        print("Secondary time interval: " + self.sec_time_entry.get())
        print("File name: " + self.file_entry.get())
        print("Baking temp: " + self.baking_temp_entry.get())
        if os.path.isfile(self.file_entry.get()):
            file_obj = open(self.file_entry.get(), "a")
            file_obj.write("Testing appending...\n")
            file_obj.close()
        else:
            file_obj = open(self.file_entry.get(), "w")
            file_obj.write("Testing writing!!!\n")
            file_obj.close()


def format_selected(flag):
    if flag == 1:
        return "On"
    else:
        return "Off"


root = tk.Tk()
app = Application(master=root)
app.mainloop()
