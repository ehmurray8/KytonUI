"""Class sets up the tkinter UI code for the options panel."""

# pylint: disable=import-error, relative-import, missing-super-argument
import os
import platform
import configparser
from tkinter import ttk
import tkinter as tk
import ui_helper as uh
import colors

BAKING = "Baking"
CAL = "Calibration"

CPARSER = configparser.ConfigParser()
CPARSER.read("prog_config.cfg")
BAKE_HEAD = "Baking"
CAL_HEAD = "Calibration"

class OptionsPanel(ttk.Frame):  # pylint: disable=too-many-ancestors, too-many-instance-attributes
    """Main Tkinter window class."""

    def __init__(self, parent, program):
        super().__init__(parent)

        # Init member vars
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
        self.set_temp = tk.DoubleVar()
        self.cooling = tk.IntVar()
        self.target_temps_entry = None
        self.program = program
        self.options_grid = ttk.Frame(self)
        self.options_grid.grid(column=1, sticky='w')

        self.chan_rows = [1, 1, 1, 1]

        # Prevent from being garbage collected
        path = r'assets\plus.png'
        if platform.system() == "Linux":
            path = "assets/plus.png"
        self.img_plus = tk.PhotoImage(file=path)

        self.create_options_grid(colors.WHITE)

    def check_config(self):
        try:
            if self.program != CAL:
                int(self.num_pts.get())
                float(self.delay.get())
                float(self.init_time.get())
                float(self.init_duration.get())
                float(self.prim_time.get())
                if not os.path.exists(self.file_name.get()) and os.path.dirname(self.file_name.get()) != "" and \
                        not os.access(os.path.dirname(self.file_name.get()), os.W_OK):
                    return False
        except ValueError:
            return False
        return True

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

    def create_options_grid(self, white):
        """Creates the grid for the user to configure options."""

        # Options Grid Init
        self.options_grid.grid_columnconfigure(1, minsize=50)
        self.options_grid.grid_columnconfigure(3, minsize=50)
        row_num = 0

        if self.program == CAL:
            self.cooling = uh.checkbox_entry(self.options_grid,
                                             "Use oven cooling function?", row_num)
            row_num += 1
            num_scans = 5
        else:
            num_scans = CPARSER.getint(BAKE_HEAD, "num_scans")


        # Number of points to average entry
        self.num_pts = uh.int_entry(self.options_grid, "Num laser scans to average:",
                                    row_num, 5, num_scans)
        row_num += 1

        if self.program == CAL:
            self.num_temp_readings = uh.int_entry(self.options_grid,
                                                  "Num temperature readings to average: ",
                                                  row_num, 10, 5)
            row_num += 1
            self.temp_interval = uh.units_entry(self.options_grid,
                                                "Time between temp readings: ",
                                                row_num, 10, "seconds", 60.0)
            row_num += 1

            self.drift_rate = uh.units_entry(self.options_grid,
                                             "Drift rate: ",
                                             row_num, 10, "mK/min", 1.0)
            row_num += 1

            self.num_cal_cycles = uh.int_entry(self.options_grid,
                                               "Num cal cycles: ",
                                               row_num, 10, 1)
            row_num += 1

            self.target_temps_entry = \
                uh.array_entry(self.options_grid,
                               "Target temps (C) [Comma Separated]", row_num,
                               10, 7, white, "130, 135")
            row_num += 1
            fname = "" #CPARSER.get(BAKE_HEAD, "file")
        else:
            set_temp = CPARSER.getfloat(BAKE_HEAD, "set_temp")
            self.set_temp = uh.double_entry(self.options_grid, "Baking Temperature ({}C): ".format(u'\u00B0'),
                                            row_num, 10, set_temp)
            row_num += 1

            # Time intervals entry
            init_delay = CPARSER.getfloat(BAKE_HEAD, "init_delay")
            self.delay = uh.units_entry(self.options_grid, "Initial program delay: ",
                                        row_num, 5, "hours", init_delay)
            row_num += 1

            init_interval = CPARSER.getfloat(BAKE_HEAD, "init_interval")
            self.init_time = uh.units_entry(self.options_grid, "Initial time interval: ",
                                            row_num, 5, "seconds", init_interval)
            row_num += 1

            init_duration = CPARSER.getfloat(BAKE_HEAD, "init_duration")
            self.init_duration = uh.units_entry(self.options_grid, "Initial interval duration: ",
                                                row_num, 5, "minutes", init_duration)
            row_num += 1

            prim_interval = CPARSER.getfloat(BAKE_HEAD, "prim_interval")
            self.prim_time = uh.units_entry(self.options_grid, "Primary time interval: ",
                                            row_num, 5, "hours", prim_interval)
            row_num += 1
            fname = CPARSER.get(BAKE_HEAD, "file")

        self.file_name = uh.file_entry(
            self.options_grid, "Excel file name: ", row_num, 50, fname)
        row_num += 1

    def create_start_btn(self, start):
        """Creates the start button in the app."""
        # Start button
        start_button = ttk.Button(self)
        start_button["text"] = "Start {}".format(self.program)
        start_button["command"] = start
        start_button.grid(row=2, column=1)
        return start_button

    def create_xcel_btn(self, create_xcel):
        """Create the button for creating the excel file."""
        xcel_btn = ttk.Button(self)
        xcel_btn["text"] = "Create Excel Spreadsheet"
        xcel_btn["command"] = create_xcel
        xcel_btn.grid(row=4, column=1)
        return xcel_btn

    def add_fbg(self, fbg_grid, col, chan):
        """Add an fbg input to the view."""
        self.chan_nums.append(chan)
        self.chan_rows[chan] += 1
        serial_num, switch_pos = uh.serial_num_entry(
            fbg_grid, self.chan_rows[chan], col, "FBG {}".format(sum(self.chan_rows) - 4))
        self.sn_ents.append(serial_num)
        self.switch_positions.append(switch_pos)

    # Need to associate everything properly when deleting
    # def minus_fbg(self, fbg_grid, col, chan):
    #    # Need to add logic to add the switches to separate lists, and then combine them at the end
    #    self.chan_nums.pop()
    #    uh.remove_serial_num_entry(fbg_grid, self.chan_rows, col)
    #    # self.sn_ents.pop()
    #    self.chan_rows[chan] -= 1

    def init_fbgs(self):
        """Initialize the fbg input section of the configuration page."""
        fbg_grid = ttk.Frame(self)
        for i in range(4):
            col_num = i * 2 + 1
            ttk.Label(fbg_grid, text="Channel {}".format(
                i + 1), style="Bold.TLabel").grid(sticky='ew', row=0, column=col_num)

            ttk.Label(fbg_grid, text="Serial Number, Switch position ").grid(
                row=1, column=col_num)

            buttons_frame = ttk.Frame(fbg_grid)
            buttons_frame.grid(sticky='ew', column=col_num, row=20)

            ttk.Button(buttons_frame, image=self.img_plus,
                       command=lambda col=col_num, chan=i: self.add_fbg(fbg_grid, col, chan)) \
                .pack(expand=True, fill="both", side="left")
            # ttk.Button(buttons_frame, image=self.img_minus,
            #             command=lambda col=col_num, chan=i: self.minus_fbg(fbg_grid, col, chan))
            #     .pack(expand=True, fill="both", side="left")

        fbg_grid.grid(row=6, column=0, columnspan=2)
