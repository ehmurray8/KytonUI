import os.path
import tkinter as tk
import threading
import time

import xlsxwriter

import create_options_panel as options_panel
import controller_340_wrapper as temp_controller
import init_instruments as init
import sm125_wrapper
import create_options_panel as options


class Application(tk.Frame):
    def __init__(self, master):
        super().__init__(master)

        self.controller, self.oven, self.gp700, self.sm125 = init.setup_instruments()
        #options_panel.create_options_grid(self, master)

        #Init member vars
        self.sm125_state = tk.IntVar()
        self.gp700_state = tk.IntVar()
        self.delta_oven_state = tk.IntVar()
        self.temp340_state = tk.IntVar()
        self.fibers_sn_arr = []
        self.row_num_sn = 0

        #Init member widgets
        self.options_grid = tk.Frame(self)
        self.options_grid.pack()

        self.num_fibers_ent = tk.Entry(self.options_grid, width=10)
        self.baking_temp_entry = tk.Entry(self.options_grid, width=10)
        self.file_entry = tk.Entry(self.options_grid, width=25)
        self.sec_time_entry = tk.Entry(self.options_grid, width=10)
        self.prim_time_entry = tk.Entry(self.options_grid, width=10)
        self.num_pts_entry = tk.Entry(self.options_grid, width=10)
        self.sn_1_ent = tk.Entry(self.options_grid, width=10)
        self.sn_2_ent = tk.Entry(self.options_grid, width=10)
        self.sn_3_ent = tk.Entry(self.options_grid, width=10)
        self.sn_4_ent = tk.Entry(self.options_grid, width=10)

        #Window setup
        master.title("Kyton Baking")
        self.menu = tk.Menu(master, tearoff=0)
        master.config(menu=self.menu)
        self.pack(side="top", fill="both", expand=True)
        options.create_options_grid(self, master)
        #self.create_fibers_sn_grid()
        self.create_start_btn()

    def create_start_btn(self):
        """Creates the start button in the app."""
        self.start_button = tk.Button(self)
        self.start_button["text"] = "Start"
        self.start_button["command"] = self.start
        self.start_button.pack()


    def start(self):
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
        temperature = temp_controller.get_temp_c(self.controller)
        temperature = float(temperature[:-3])

        amplitudes_avg = []
        wavelengths_avg = []
        count = 0
        
        need_init = False
        
        while (count < int(self.num_pts_entry.get())):
            wavelengths, amplitudes = sm125_wrapper.get_data_actual(self.sm125)

            if not need_init:
                wavelengths_avg = [0] * len(wavelengths[0])
                amplitudes_avg = [0] * len(amplitudes[0])
                need_init = True
            
            i = 0
            for wll in wavelengths:
                for wl in wll: 
                    wavelengths_avg[i] += wl
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

        self.write_csv_file(serial_nums, timestamp, temperature, wavelengths_avg, amplitudes_avg)


    def write_csv_file(self, serial_nums, time, temp, wavelengths, powers):
        if os.path.isfile(self.file_entry.get() + ".csv"):
            file_obj = open(self.file_entry.get() + ".csv", "a")
        else:
            file_obj = open(self.file_entry.get() + ".csv", "w")

        file_obj.write("Serial Num, Timestamp(s), Temperature (C), Wavelength (pm), Power (db)\n")
        file_obj.write("----------------------------------------------------------------------\n")

        i = 0
        while i < len(serial_nums):
            file_obj.write(str(serial_nums[i]) + ": " + str(time) + ", " + str(temp) + ", " +\
                           str(wavelengths[i]) + ", " + str(powers[i]) + "\n")
            i += 1

        file_obj.write("\n\n")
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
