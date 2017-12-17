"""Class sets up the tkinter UI code for the options panel."""

# pylint: disable=import-error, relative-import, missing-super-argument
import os
from tkinter import messagebox as mbox
import platform
import configparser
from tkinter import ttk
import tkinter as tk
import ui_helper as uh
import colors
import helpers as help

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
        self.sn_ents = [[], [], [], []]
        self.chan_nums = [[], [], [], []]
        self.switch_positions = [[], [], [], []]
        self.snum_frames = [[], [], [], []]

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
        self.fbg_grid = ttk.Frame(self)

        self.chan_rows = [1, 1, 1, 1]

        # Prevent from being garbage collected
        path = r'assets\plus.png'
        if platform.system() == "Linux":
            path = "assets/plus.png"
        self.img_plus = tk.PhotoImage(file=path)

        path = r'assets\minus.png'
        if platform.system() == "Linux":
            path = "assets/minus.png"
        self.img_minus = tk.PhotoImage(file=path)

        self.create_options_grid(colors.WHITE)

    def check_config(self):
        try:
            if self.program != CAL:
                int(self.num_pts.get())
                float(self.delay.get())
                float(self.init_time.get())
                float(self.init_duration.get())
                float(self.prim_time.get())

                path, fname = os.path.split(self.file_name.get())
                fname, ext = os.path.splitext(fname)
                if not path or ext != ".xlsx" or not fname:
                    mbox.showerror("Invalid configuration",
                                   "Please insert a proper file name that has the extension .xlsx.")
                    return False

                if not os.path.exists(self.file_name.get()) and os.path.dirname(self.file_name.get()) != "" and \
                        not os.access(os.path.dirname(self.file_name.get()), os.W_OK):
                    mbox.showerror("Invalid configuration",
                                   "Please check the file path, the file cannot be opened or created.")
                    return False
        except ValueError:
            mbox.showerror("Invalid configuration",
                           "Please check to make sure the configuration settings are numeric.")
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

    def add_fbg(self, fbg_grid, col, chan, fbg_name=None, switch_pos=None):
        """Add an fbg input to the view."""
        most = -1
        for i, chan_num in enumerate(self.chan_nums):
            if len(chan_num) > 1:
                most = i
        if len(self.chan_nums[chan]) >= 16:
            mbox.showerror("Channel error", "Can only have 16 FBGs on single channel.")
        elif most != -1 and most != chan and len(self.chan_nums[chan]):
            mbox.showerror("Channel error", "Can only have multiple FBGs on a single channel, please clear channel {} "
                           .format(most + 1) + " before continuing.")
        else:
            self.chan_nums[chan].append(chan)
            def_name = "FBG {}".format(sum(len(x) for x in self.chan_nums))
            if fbg_name is not None:
                def_name = fbg_name
            serial_num, switch_pos, frame = uh.serial_num_entry(
                fbg_grid, len(self.chan_nums[chan])+1, col, def_name, switch_pos)
            self.snum_frames[chan].append(frame)
            self.sn_ents[chan].append(serial_num)
            self.switch_positions[chan].append(switch_pos)

    def minus_fbg(self, chan):
        if len(self.chan_nums[chan]):
            self.chan_nums[chan].pop()
            uh.remove_snum_entry(self.snum_frames[chan][-1])
            self.sn_ents[chan].pop()
            self.switch_positions[chan].pop()

    def init_fbgs(self):
        """Initialize the fbg input section of the configuration page."""
        for i in range(4):
            col_num = i * 2 + 1
            ttk.Label(self.fbg_grid, text="Channel {}".format(
                i + 1), style="Bold.TLabel").grid(sticky='ew', row=0, column=col_num)

            ttk.Label(self.fbg_grid, text="Serial Number, Switch position ").grid(
                row=1, column=col_num)

            buttons_frame = ttk.Frame(self.fbg_grid)
            buttons_frame.grid(sticky='ew', column=col_num, row=20)

            ttk.Button(buttons_frame, image=self.img_minus,
                       command=lambda chan=i: self.minus_fbg(chan)) \
               .pack(expand=True, fill="both", side="left")
            ttk.Button(buttons_frame, image=self.img_plus,
                       command=lambda col=col_num, chan=i: self.add_fbg(self.fbg_grid, col, chan)) \
                .pack(expand=True, fill="both", side="left")

        self.fbg_grid.grid(row=6, column=0, columnspan=2)
        if self.program == CAL:
            pass
        else:
            for i in range(4):
                snums = CPARSER.get(BAKE_HEAD, "chan{}_fbgs".format(i+1)).split(",")
                positions = CPARSER.get(BAKE_HEAD, "chan{}_positions".format(i+1)).split(",")
                try:
                    positions = help.list_cast(positions, int)
                    for snum, pos in zip(snums, positions):
                        self.add_fbg(self.fbg_grid, i * 2 + 1, i, snum, pos)
                except ValueError:
                    for snum in snums:
                        if snum:
                            self.add_fbg(self.fbg_grid, i*2+1, i, snum)

