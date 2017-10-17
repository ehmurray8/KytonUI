"""Class sets up the tkinter UI code for the options panel."""

# pylint: disable=import-error, relative-import, missing-super-argument
from tkinter import ttk
import tkinter as tk
import ui_helper as uh

BAKING = "Baking"
CAL = "Cal"


class OptionsPanel(tk.Frame):   # pylint: disable=too-many-ancestors
                                # pylint: disable=too-many-instance-attributes
    """Main Tkinter window class."""

    def __init__(self, master, num_sns, program):
        super().__init__(master)

        # Init member vars
        self.sm125_state = tk.IntVar()
        self.op_switch_state = tk.IntVar()
        self.delta_oven_state = tk.IntVar()
        self.temp340_state = tk.IntVar()
        self.sn_ents = []
        self.chan_nums = []
        self.switch_positions = []

        # Init member widgets
        self.baking_temp = tk.DoubleVar()
        self.file_name = tk.StringVar()
        self.delay = tk.DoubleVar()
        self.init_time = tk.DoubleVar()
        self.init_duration = tk.DoubleVar()
        self.prim_time = tk.DoubleVar()
        self.num_pts = tk.IntVar()
        self.num_temp_readings = tk.IntVar()
        self.temp_interval = tk.IntVar()
        self.drift_rate = tk.DoubleVar()
        self.num_cal_cycles = tk.IntVar()
        self.cooling = tk.IntVar()
        self.target_temps_entry = None

        self.create_options_grid(program, num_sns)

    def get_target_temps(self):
        """
        Returns the target temps as an array, returns None if formatting of
        Text widget is wrong.
        """
        target_temps_str = self.target_temps_entry.get(1.0, tk.END)
        target_temps_arr = target_temps_str.split(",")
        try:
            target_temps_arr = [int(x) for x in target_temps_arr]
        except ValueError:
            return None

        return target_temps_arr

    def create_options_grid(self, program, num_sns):
        """Creates the grid for the user to configure options."""
        self.pack(side="top", fill="both", expand=True)

        options_grid = tk.Frame(self)
        options_grid.pack()

        # Options Grid Init
        options_grid.grid_columnconfigure(1, minsize=50)
        options_grid.grid_columnconfigure(3, minsize=50)
        row_num = 0

        # Instruments Checkboxes
        self.sm125_state = uh.checkbox_entry(options_grid,
                                             "Micron Optics SM125", row_num)
        row_num += 1

        self.op_switch_state = uh.checkbox_entry(options_grid,
                                                 "Optical Switch", row_num)
        row_num += 1

        self.temp340_state = uh.checkbox_entry(options_grid, "340 Controller",
                                               row_num)
        row_num += 1

        self.delta_oven_state = uh.checkbox_entry(options_grid, "Delta Oven",
                                                  row_num)
        row_num += 1

        if program == CAL:
            self.cooling = uh.checkbox_entry(options_grid,
                                             "Use oven cooling function?",
                                             row_num)
            row_num += 1

        # Number of points to average entry
        self.num_pts = uh.int_entry(options_grid,
                                    "Num laser scans to average:", row_num,
                                    10, 5)
        row_num += 1

        if program == CAL:
            # self.num_temp_readings = uh.int_entry(options_grid,
            #                      "Num temperature readings to average: ", \
            #                                            row_num, 10, 5)
            # row_num += 1
            self.temp_interval = uh.time_entry(options_grid,
                                               "Time between temp readings: ",
                                               row_num, 10, "seconds", 60.0)
            row_num += 1

            self.drift_rate = uh.double_entry(options_grid,
                                              "Drift rate (mK/min): ",
                                              row_num, 10, 1.0)
            row_num += 1

            self.num_cal_cycles = uh.int_entry(options_grid,
                                               "Num cal cycles: ",
                                               row_num, 10, 1)
            row_num += 1

            self.target_temps_entry = \
                uh.array_entry(options_grid,
                               "Target temps (C) [Comma Separated]", row_num,
                               10, 7, "130, 135")
            row_num += 1
        else:
            # Time intervals entry
            self.delay = uh.time_entry(options_grid, "Initial program delay: ",
                                       row_num, 10, "hours", 1.0)
            row_num += 1

            self.init_time = uh.time_entry(options_grid, "Initial time interval: ",
                                           row_num, 10, "seconds", 15.0)
            row_num += 1

            self.init_duration = uh.time_entry(options_grid, "Initial interval duration: ",
                                               row_num, 10, "minutes", 5.0)
            row_num += 1

            self.prim_time = uh.time_entry(options_grid, "Primary time interval: ",
                                           row_num, 10, "hours", 1.0)
            row_num += 1

        self.file_name = uh.file_entry(options_grid, "Excel file name: ", row_num, 30)
        row_num += 1

        if program == BAKING:
                # Baking setpoint entry
            self.baking_temp = uh.double_entry(options_grid, "Baking temp: ",
                                               row_num, 10, 250.0)
            row_num += 1

        # (TEMP) Fiber SN Inputs
        index = 1
        while index <= num_sns:
            serial_num, chan_num, switch_pos = \
                uh.serial_num_entry(options_grid,
                                    "Serial Number " + str(index) + ": ",
                                    row_num, 5, "FBG " + str(index))
            self.sn_ents.append(serial_num)
            self.chan_nums.append(chan_num)
            self.switch_positions.append(switch_pos)

            index += 1
            row_num += 1

    def create_start_btn(self, start):
        """Creates the start button in the app."""
        # Start button
        start_button = ttk.Button(self)
        start_button["text"] = "Start"
        start_button["command"] = start
        start_button.pack(pady=10)
        return start_button
