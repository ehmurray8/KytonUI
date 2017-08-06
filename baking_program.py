#pylint:disable=unused-import, wrong-import-position
"""Main entry point for the UI."""
import tkinter as tk
from tkinter import ttk
from tkinter import messagebox
import configparser
import time
import sys
import pyvisa as visa

import matplotlib
import matplotlib.animation as animation
from matplotlib import style
from matplotlib.figure import Figure
import matplotlib.pyplot as plt

import controller_340_wrapper as temp_controller
import delta_oven_wrapper as oven_wrapper
import sm125_wrapper
import create_options_panel as options_panel
import file_helper
import graphing_helper

style.use('ggplot')

NUM_SNS = 4
TERM_CHAR = '/n'

CPARSER = configparser.SafeConfigParser()
CPARSER.read("devices.cfg")

class Application(tk.Frame): # pylint: disable=too-many-ancestors, too-many-instance-attributes
    """Class containing the main tkinter application."""
    def __init__(self, master):
        """Constructs the app."""
        super().__init__(master)

        self.controller = None
        self.oven = None
        self.gp700 = None
        self.sm125 = None

        #Window setup
        master.title("Kyton Baking")
        self.menu = tk.Menu(master, tearoff=0)
        master.config(menu=self.menu)
        self.menu.add_command(label="Create Excel", command=lambda: \
                file_helper.create_excel_file(self.options.file_name.get()))
        self.menu.add_command(label="Show Graph", command=lambda: \
                graphing_helper.create_mean_wave_time_graph(self.options.file_name.get()))
        self.menu.add_command(label="Show Graph 1", command=lambda: \
                graphing_helper.create_wave_power_graph(self.options.file_name.get()))
        self.menu.add_command(label="Config", command=update_config)

        self.pack(side="top", fill="both", expand=True)
        self.main_frame = tk.Frame(self)
        self.options = options_panel.OptionsPanel(self.main_frame)
        self.options.create_start_btn(self.start)
        self.options.grid(row=0, column=0, sticky='ew')

        self.stable_count = 0

        self.main_frame.pack(expand=1, fill=tk.BOTH)


    def animate(self, i):
        """Updates the graph."""
        print("Animate " + str(i) + " " + str(self.num_pt))
        self.x_vals.append(self.num_pt)
        self.y_vals.append(self.num_pt)
        self.num_pt += 1
        self.line.set_data(self.x_vals, self.y_vals)
        return self.line,

    def create_excel(self):
        """Creates excel file."""
        file_helper.create_excel_file(self.options.file_name.get())

    def start(self):
        """Starts the recording process."""
        if len(sys.argv) > 1 and sys.argv[1] == "-k":
            resource_manager = visa.ResourceManager()
            if self.options.temp340_state.get():
                controller_location = "GPIB0::{}::INSTR".format(CPARSER.get("Devices", \
                                                                "controller_location"))
                self.controller = resource_manager.open_resource(controller_location, \
                        read_termination=TERM_CHAR)
            if self.options.delta_oven_state.get():
                oven_location = "GPIB0::{}::INSTR".format(CPARSER.get("Devices", \
                                                          "oven_location"))
                self.oven = resource_manager.open_resource(oven_location, \
                        read_termination=TERM_CHAR)
                oven_wrapper.set_temp(self.oven, self.options.baking_temp.get())
            if self.options.gp700_state.get():
                gp700_location = "GPIB0::{}::INSTR".format(CPARSER.get("Devices", \
                                                           "gp700_location"))
                self.gp700 = resource_manager.open_resource(gp700_location,\
                        read_termination=TERM_CHAR)
            if self.options.sm125_state.get():
                sm125_address = CPARSER.get("Devices", "sm125_sm125_address")
                sm125_port = CPARSER.get("Devices", "sm125_port")
                self.sm125 = sm125_wrapper.setup(sm125_address, sm125_port)
        sm125_address = CPARSER.get("Devices", "sm125_address")
        sm125_port = CPARSER.get("Devices", "sm125_port")
        print(sm125_address)
        print(sm125_port)
        CPARSER.set("Devices", "sm125_address", "69")
        with open("devices.cfg", "w+") as conf:
            CPARSER.write(conf)
        print(CPARSER.get("Devices", "sm125_address"))

        self.program_loop()

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
        print("Started program loop...")
        if not self.check_stable():
            self.baking_loop()
            self.after(int(self.options.init_time.get()) * 1000, self.program_loop)
        else:
            self.baking_loop()
            self.after(int(self.options.prim_time.get()) * 1000 * 60, self.program_loop)

    def __avg_waves_amps(self):
        amplitudes_avg = []
        wavelengths_avg = []
        count = 0
        need_init = False
        while count < int(self.options.num_pts.get()):
            #wavelengths, amplitudes = sm125_wrapper.get_data_channels(self.options.chan_nums)
            #TODO
            #Need to associate proper amplitudes/powers with correct serial number
            if len(sys.argv) > 1 and sys.argv[1] == "-k":
                wavelengths, amplitudes = sm125_wrapper.get_data_actual(self.sm125)
            else:
                wavelengths = [[]]
                amplitudes = [[]]

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
        return wavelengths_avg, amplitudes_avg


    def baking_loop(self):
        """Runs the baking process."""
        print("Started baking loop...")

        if len(sys.argv) > 1 and sys.argv[1] == "-k":
            temperature = temp_controller.get_temp_c(self.controller)
            temperature = float(temperature[:-3])
        else:
            temperature = 0

        wavelengths_avg, amplitudes_avg = self.__avg_waves_amps()

        if len(sys.argv) > 1 and sys.argv[1] == "-k":
            temp2 = temp_controller.get_temp_c(self.controller)
            temperature += float(temp2[:-3])

        temperature /= 2.0

        serial_nums = []
        for sn_ent in self.options.sn_ents:
            serial_nums.append(sn_ent.get())

        curr_time = time.time()

        if len(sys.argv) > 1 and sys.argv[1] == "-k":
            file_helper.write_csv_file(self.options.file_name.get(), serial_nums, \
                    curr_time, temperature, wavelengths_avg, amplitudes_avg)


def start_bake(popup, inpt):
    """Starts the baking program."""
    #pylint:disable=global-statement
    global ROOT, NUM_SNS
    number = inpt.get()
    try:
        NUM_SNS = int(number)
        options_panel.NUM_SNS = int(number)
        popup.destroy()
        ROOT = tk.Tk()
        app = Application(master=ROOT)
        #open_center(750, 600, ROOT)
        app.mainloop()
    except ValueError:
        messagebox.showwarning("Invalid Input", "Please input an integer.")

def update_config():
    """Updates devices configuration."""
    cont_loc = CPARSER.get("Devices", "controller_location")
    oven_loc = CPARSER.get("Devices", "oven_location")
    gp700_loc = CPARSER.get("Devices", "gp700_location")
    sm125_addr = CPARSER.get("Devices", "sm125_address")
    sm125_port = CPARSER.get("Devices", "sm125_port")


    popup = tk.Toplevel()
    popup.wm_title("Device Configuration")
    frame = tk.Frame(popup)
    frame.pack()
    config_grid = tk.Frame(frame)
    config_grid.pack(side="top", fill="both", expand=True)

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

    ttk.Button(frame, text="Save", command=lambda: save_config(cont_ent, oven_ent, \
            gp700_ent, sm125_addr_ent, sm125_port_ent, popup)). \
            pack(side="top", fill="both", expand=True, pady=10)

    open_center(350, 150, popup)
    popup.protocol("WM_DELETE_WINDOW", lambda: __on_closing(popup))

def __on_closing(root):
    if messagebox.askokcancel("Quit", "Changes won't be save. Are you sure you want to quit?"):
        root.destroy()
    else:
        root.tkraise()


def save_config(cont_ent, oven_ent, gp700_ent, sm125_addr_ent, sm125_port_ent, window):
    #pylint:disable=too-many-arguments
    """Save configuration data to config file."""
    addr_str = sm125_addr_ent.get()
    addrs = addr_str.split(".")
    try:
        cont_loc = int(cont_ent.get())
        oven_loc = int(oven_ent.get())
        gp700_loc = int(gp700_ent.get())
        port = int(sm125_port_ent.get())
        for addr in addrs:
            int(addr)
    except ValueError:
        messagebox.showwarning("Invalid Input", "GPIB0 port entries require integers. \
                                                    \nIP port requires an integer. \
                                                    \nIP address requires #.#.#.#")


    CPARSER.set("Devices", "controller_location", str(cont_loc))
    CPARSER.set("Devices", "oven_location", str(oven_loc))
    CPARSER.set("Devices", "gp700_location", str(gp700_loc))
    CPARSER.set("Devices", "sm125_address", str(addr_str))
    CPARSER.set("Devices", "sm125_port", str(port))
    with open("devices.cfg", "w+") as conf:
        CPARSER.write(conf)
    window.destroy()


def open_center(width, height, root):
    #pylint:disable=global-statement
    """Open num fiber dialog in center of the screen."""
    width_screen = root.winfo_screenwidth()
    height_screen = root.winfo_screenheight()

    x_cord = (width_screen/2) - (width/2)
    y_cord = (height_screen/2) - (height/2)

    root.geometry("{}x{}-{}+{}".format(int(width), int(height),\
                             int(x_cord), int(y_cord)))

def launch():
    """Launches Dialog box to input number of fibers."""
    num_sns_root = tk.Tk()
    tk.Label(num_sns_root, text="How many fibers will be used for baking? ").\
             pack(side="top", expand=True, padx=10, pady=5)
    inpt = ttk.Entry(num_sns_root, width=10, justify="center")
    inpt.pack(side="top", padx=10, pady=5, expand=True)
    ttk.Button(num_sns_root, text="Start Baking", command=lambda: start_bake(num_sns_root, inpt))\
            .pack(side="top", expand=True, padx=10, pady=5)
    num_sns_root.title("Baking Settings")
    open_center(275, 125, num_sns_root)
    num_sns_root.mainloop()


if __name__ == "__main__":
    ROOT = None
    launch()
