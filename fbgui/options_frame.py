"""Class sets up the tkinter UI code for the options screen."""

import configparser
import os
import tkinter as tk
from tkinter import messagebox as mbox
from tkinter import ttk
from typing import List, Callable

from fbgui import helpers, ui_helper as uh, reset_config
from fbgui.constants import BAKING, CAL, ASSETS_PATH


class OptionsPanel(ttk.Frame):
    """
    Options panel widget in both the baking and calibration program screens, used for configuring program settings.

    :ivar List[List[tkinter.Entry]] sn_ents: 2D list with one list for each SM125 channel, of tkinter Entrys
                                             corresponding to the serial number input fields
    :ivar List[List[int]] chan_nums: 2D list with one list for each SM125 channel, of ints where the len of the lists
                                     is used for determining the number of FBGs on a channel
    :ivar List[List[tkinter.IntVar]] switch_positions: 2D list with one list for each SM125 channel, of tkinter
                                                       IntVars each representing a ttk spinbox used for specifying
                                                       the FBGs switch position
    :ivar List[List[tk.IntVar]] selected_fbgs: 2D list with one list for each SM125 channel, of IntVars, which are used
                                               to watch the value of the CheckButtons in each fbg frame
    :ivar List[List[tkinter.Frame]] snum_frames: 2D list with one list for each SM125 channel, of tkinter Frames, each
                                                 Frame contains a serial number, and switch input for a FBG
    :ivar tkinter.StringVar file_name: tkinter StringVar corresponding to the file input
    :ivar tkinter.DoubleVar prim_time: tkinter DoubleVar corresponding to the primary bake time
    :ivar tkinter.IntVar num_pts: tkinter IntVar corresponding to the number of points to average for each reading
    :ivar tkinter.IntVar num_temp_readings: the number of temperature readings to use to average for the
                                            calibration program
    :ivar tkinter.IntVar temp_interval: IntVar corresponding to the time between taking cal drift rate readings
    :ivar tkinter.DoubleVar drift_rate: IntVar corresponding to the maximum calibration point drift rate
    :ivar tkinter.IntVar num_cal_cycles: IntVar corresponding to the number of calibration cycles to run
    :ivar tkinter.IntVar cooling: IntVar - 1 if cal program is configured to use cooling, 0 if not configured to use
                                           cooling
    :ivar tkinter.Text target_temps_entry: Text entry corresponding to the calibration target temperatures text input
    :ivar tkinter.Frame options_grid: Upper portion of the options screen containing configuration options
    :ivar tkinter.Frame fbg_grid: Lower portion of the options screen containing fbg configuration options
    :ivar configparser.ConfigParser conf_parser: ConfigParser used for reading in prog_config settings
    """

    def __init__(self, parent: ttk.Frame, program: str):
        super().__init__(parent)

        self.sn_ents = [[], [], [], []]  # type: List[List[tk.Entry]]
        self.chan_nums = [[], [], [], []]  # type: List[List[int]]
        self.switch_positions = [[], [], [], []]  # type: List[List[tk.IntVar]]
        self.snum_frames = [[], [], [], []]  # type: List[List[ttk.Frame]]
        self.selected_fbgs = [[], [], [], []]  # type: List[List[tk.IntVar]]

        self.extra_points = []  # type: List[List[tk.DoubleVar]]

        self.file_name = tk.StringVar()
        self.prim_time = tk.DoubleVar()
        self.num_pts = tk.IntVar()
        self.num_temp_readings = tk.IntVar()
        self.temp_interval = tk.IntVar()
        self.drift_rate = tk.DoubleVar()
        self.num_cal_cycles = tk.IntVar()
        self.set_temp = tk.DoubleVar()
        self.cooling = tk.IntVar()
        self.bake_sensitivity = tk.DoubleVar()
        self.target_temps_entry = None  # type: tk.Text
        self.program = program
        self.options_grid = ttk.Frame(self)

        self.conf_parser = configparser.ConfigParser()
        self.conf_parser.read(os.path.join("config", "prog_config.cfg"))

        if self.program == BAKING:
            text = "Configure Baking Run"
            ttk.Label(self, text=text).pack(anchor="center", pady=20)
        else:
            text = "Configure Calibration Run"
            header = ttk.Frame(self)
            header.pack(anchor=tk.W, pady=5)
            ttk.Label(header, text=text).pack(anchor=tk.W, side=tk.LEFT)
            try:
                use_cool = self.conf_parser.getboolean(self.program, "use_cool")
            except configparser.NoOptionError:
                use_cool = False
            self.cooling = tk.IntVar()
            ttk.Label(header, text="Use oven cooling function?").pack(side=tk.LEFT, padx=50)
            checkbox = ttk.Checkbutton(header, variable=self.cooling, width=5)
            checkbox.pack(side=tk.LEFT)
            if use_cool:
                checkbox.invoke()
        self.options_grid.pack(expand=True, fill="both", anchor="center")
        self.fbg_grid = ttk.Frame(self)
        self.fbg_grid.pack(expand=True, fill="both", anchor="n")

        # Prevent from being garbage collected
        path = os.path.join(ASSETS_PATH, 'plus.png')
        self.img_plus = tk.PhotoImage(file=path)
        path = os.path.join(ASSETS_PATH, 'minus.png')
        self.img_minus = tk.PhotoImage(file=path)

        try:
            self.create_options_grid()
        except configparser.NoSectionError:
            reset_config.reset_config(rewrite_program=True)
            mbox.showerror("Internal error", "Please restart the program.")

    def check_config(self, db_controller) -> bool:
        """
        Checks to make sure all of the input fields are filled in properly, and of the right types.

        **
        This does not ensure the configuration settings make sense, just that the fields have values of the proper
        type.
        **

        :param db_controller fbgui.DatabaseController
        :return True if properly configured, False otherwise
        """
        try:
            int(self.num_pts.get())
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
            if self.program == BAKING:
                float(self.prim_time.get())
            else:
                float(self.num_temp_readings.get())
                float(self.temp_interval.get())
                float(self.drift_rate.get())
                float(self.num_cal_cycles.get())

            fbg_names = [fbg_name.get() for snum_list in self.sn_ents for fbg_name in snum_list]

            if len(fbg_names) != len(set(fbg_names)):
                mbox.showerror("Invalid configuration", "Multiple FBGs have the same name.")
                return False
            stored_fbg_names = db_controller.get_fbg_list()
            if len(stored_fbg_names) > 0 and set(fbg_names) != set(stored_fbg_names):
                mbox.showerror("Invalid configuration",
                               "The fbg names have changed since the last time the program was run, "
                               "please start the program with a new file name.")
                return False
        except (ValueError, tk.TclError):
            mbox.showerror("Invalid configuration",
                           "Please check to make sure the configuration settings are numeric.")
            return False

        if self.program == CAL:
            try:
                self.get_target_temps()
            except (ValueError, tk.TclError):
                mbox.showerror("Configuration Error",
                               "The target temperatures import is not formatted properly, please insert the target " +
                               "temps as comma separated decimal numbers.")
                return False

            for i, (temperature, wavelength_text, power_text) in enumerate(self.extra_points):
                try:
                    float(temperature.get())
                except ValueError:
                    mbox.showerror("Configuration Error", "Extra point {} has an invalid temperature.".format(i+1))
                    return False

                if temperature.get() != 0:
                    if not self.check_extra_point(wavelength_text, i + 1, "wavelengths") or \
                            not self.check_extra_point(power_text, i + 1, "powers"):
                        return False
        return True

    def check_extra_point(self, text: tk.Text, point_num: int, input_type: str) -> bool:
        not_enough_error = str("Extra point {} doesn't have the same amount of {} as there are fbgs. To get a better "
                               "view of the elements in the text box click on the unit label to the right of the text "
                               "box.").format(point_num, input_type)
        invalid_error = str("Extra point {} has invalid {}, ensure that all the values in the text box are "
                            "decimal numbers. To get a better view of the elements in the text box click on the unit "
                            "label to the right of the text box.").format(point_num, input_type)
        error_title = "Configuration Error"
        number_of_fbgs = sum(len(x) for x in self.sn_ents)
        try:
            values = [float(x) for x in text.get(1.0, tk.END).split(",")]
            if len(values) != number_of_fbgs:
                mbox.showerror(error_title, not_enough_error)
                return False
        except ValueError:
            mbox.showerror(error_title, invalid_error)
            return False
        return True

    def get_target_temps(self) -> List[float]:
        """
        Returns the target temps as an array, doesn't catch the ValueError exception possibility.

        :return: list of target calibration temps
        :raises ValueError: If target temps are not of the right type
        """
        return helpers.list_cast(self.target_temps_entry.get(1.0, tk.END).split(","), float)

    def create_options_grid(self):
        """Creates the grid for the user to configure options, in the upper portion of the options screen."""

        row_num = 0
        try:
            num_scans = self.conf_parser.getint(self.program, "num_scans")
        except configparser.NoOptionError:
            num_scans = 1
        self.num_pts = uh.int_entry(self.options_grid, "Num laser scans to average:", row_num, 5, num_scans)
        row_num += 1

        if self.program == CAL:
            try:
                num_readings = self.conf_parser.getint(self.program, "num_temp_readings")
            except configparser.NoOptionError:
                num_readings = 1
            self.num_temp_readings = uh.int_entry(self.options_grid, "Num temperature readings to average: ",
                                                  row_num, 10, num_readings)
            row_num += 1

            try:
                temp_int = self.conf_parser.getfloat(self.program, "temp_interval")
            except configparser.NoOptionError:
                temp_int = 1.0

            self.temp_interval = uh.units_entry(self.options_grid, "Time between temp readings: ", row_num, 10,
                                                "seconds", temp_int)
            row_num += 1

            try:
                drate = self.conf_parser.getfloat(self.program, "drift_rate")
            except configparser.NoOptionError:
                drate = 5.0

            self.drift_rate = uh.units_entry(self.options_grid, "Drift rate: ", row_num, 10, "mK/min", drate)
            row_num += 1

            try:
                num_cycles = self.conf_parser.getint(self.program, "num_cycles")
            except configparser.NoOptionError:
                num_cycles = 1

            self.num_cal_cycles = uh.int_entry(self.options_grid, "Num cal cycles: ", row_num, 10, num_cycles)
            row_num += 1

            try:
                target_temps = self.conf_parser.get(self.program, "target_temps")
            except configparser.NoOptionError:
                target_temps = ""
            self.target_temps_entry = uh.array_entry(self.options_grid, "Target temps {}C [Comma Separated]"
                                                     .format(u'\u00B0'), row_num, width=10, height=1,
                                                     default_arr=target_temps)
            row_num += 1
            self.add_extra_point(row_num, "1")
            row_num += 1
            self.add_extra_point(row_num, "2")
            row_num += 1
        else:
            try:
                set_temp = self.conf_parser.getfloat(self.program, "set_temp")
            except configparser.NoOptionError:
                set_temp = 0.0
            self.set_temp = uh.double_entry(self.options_grid, "Baking Temperature ({}C): ".format(u'\u00B0'),
                                            row_num, 10, set_temp)
            row_num += 1

            try:
                drate = self.conf_parser.getfloat(self.program, "drift_rate")
            except configparser.NoOptionError:
                drate = 5.0
            self.drift_rate = uh.units_entry(self.options_grid, "Drift rate: ", row_num, 10, "mK/min", drate)
            row_num += 1

            try:
                prim_interval = self.conf_parser.getfloat(self.program, "prim_interval")
            except configparser.NoOptionError:
                prim_interval = 1.0

            self.prim_time = uh.units_entry(self.options_grid, "Primary time interval: ", row_num, 5,
                                            "hours", prim_interval)
            row_num += 1

            try:
                bake_sensitivity = self.conf_parser.getfloat(self.program, "bake_sensitivity")
            except configparser.NoOptionError:
                bake_sensitivity = 0.0
            self.bake_sensitivity = uh.units_entry(self.options_grid, "Bake Sensitivity: ", row_num, 5,
                                                   "pm/K", bake_sensitivity)
            row_num += 1

        fname = self.conf_parser.get(self.program, "file")
        self.file_name = uh.file_entry(self.options_grid, "Excel file name: ", row_num, 50, fname)
        row_num += 1

    def add_extra_point(self, row_num: int, point_num: str):
        try:
            saved_temperature = self.conf_parser.get(self.program, "extra_point{}_temperature".format(point_num))
        except configparser.NoOptionError:
            saved_temperature = 0.0
        try:
            saved_temperature = float(saved_temperature)
        except ValueError:
            saved_temperature = 0.0

        temperature, wavelength, power = uh.extra_point_entry(self.options_grid, "Extra Point {}".format(point_num),
                                                              row_num, saved_temperature)
        try:
            saved_wavelengths = self.conf_parser.get(self.program, "extra_point{}_wavelengths".format(point_num))
        except configparser.NoOptionError:
            saved_wavelengths = ""
        try:
            [float(x) for x in saved_wavelengths.split(",")]
        except ValueError:
            saved_wavelengths = ""

        try:
            saved_powers = self.conf_parser.get(self.program, "extra_point{}_powers".format(point_num))
        except configparser.NoOptionError:
            saved_powers = ""
        try:
            [float(x) for x in saved_powers.split(",")]
        except ValueError:
            saved_powers = ""

        self.extra_points.append([temperature, wavelength, power])
        wavelength.insert(1.0, saved_wavelengths)
        power.insert(1.0, saved_powers)

    def create_start_btn(self, start: Callable) -> ttk.Button:
        """
        Creates the start button in the app, and adds the start parameter as the button callback.

        :return: the created tkinter Button
        """
        start_button = ttk.Button(self)
        title = self.program
        if title == CAL:
            title = "Calibration"
        start_button["text"] = "Start {}".format(title)
        start_button["command"] = start
        start_button.pack(anchor='center', pady=20)
        return start_button

    def add_fbg(self, chan: int, fbg_name: str=None, switch_pos: int=None):
        """
        Add an fbg input to the view, at the column corresponding to the chan index. If fbg_name, and switch_pos
        are not None then set the serial number entry, and switch position entry to their values respectively.

        :param chan: index of where the new fbg sub frame should be added
        :param fbg_name: If not None, the name of the FBG to add
        :param switch_pos: If not None, the switch position of the FBG to add
        """
        if len(self.chan_nums[chan]) >= 16:
            mbox.showerror("Channel error", "Can only have 16 FBGs on single channel.")
        else:
            self.chan_nums[chan].append(chan)
            def_name = "FBG {}".format(sum(len(x) for x in self.chan_nums))
            if fbg_name is not None:
                def_name = fbg_name
            serial_num, switch_pos, frame, selected = uh.serial_num_entry(self.fbg_grid, len(self.chan_nums[chan])+1,
                                                                          chan, def_name, switch_pos)
            self.selected_fbgs[chan].append(selected)
            self.snum_frames[chan].append(frame)
            self.sn_ents[chan].append(serial_num)
            self.switch_positions[chan].append(switch_pos)

    def minus_fbg(self, chan: int):
        """
        Removes the last FBG sub frame at the specified chan index.

        :param chan: index of which column to remove a FBG sub frame from
        """
        need_refresh = False
        positions_to_remove = []
        for i, selected in enumerate(self.selected_fbgs[chan]):
            if selected.get():
                need_refresh = True
                positions_to_remove.append(i)

        for i in reversed(positions_to_remove):
            del self.chan_nums[chan][i]
            frame = self.snum_frames[chan][i]
            uh.remove_snum_entry(frame)
            del self.snum_frames[chan][i]
            del self.sn_ents[chan][i]
            del self.switch_positions[chan][i]
            del self.selected_fbgs[chan][i]

        if need_refresh:
            for frame in self.snum_frames[chan]:
                uh.remove_snum_entry(frame)

            channel_numbers = [x for x in self.chan_nums[chan]]
            snum_entries = [x for x in self.sn_ents[chan]]
            switch_positions = [x for x in self.switch_positions[chan]]

            self.chan_nums[chan].clear()
            self.snum_frames[chan].clear()
            self.sn_ents[chan].clear()
            self.switch_positions[chan].clear()
            self.selected_fbgs[chan].clear()

            for channel_number, snum_entry, switch_position in zip(channel_numbers, snum_entries, switch_positions):
                self.add_fbg(channel_number, snum_entry.get(), switch_position.get())

    def init_fbgs(self):
        """ Initialize the fbg input section of the options page, using settings stored in prog_config."""
        for i in range(4):
            title_frame = ttk.Frame(self.fbg_grid)
            ttk.Label(title_frame, text="Channel {}".format(i + 1), style="Bold.TLabel")\
                .pack(side='left', anchor='w')

            buttons_frame = ttk.Frame(title_frame)
            ttk.Button(buttons_frame, image=self.img_minus, command=lambda chan=i: self.minus_fbg(chan)) \
                .pack(side="left", anchor='e')
            ttk.Button(buttons_frame, image=self.img_plus,
                       command=lambda col=i, chan=i: self.add_fbg(chan)).pack(side='left', anchor='e')
            buttons_frame.pack(anchor='e')
            title_frame.grid(sticky='nsew', column=i, row=0)

        for i in range(4):
            try:
                try:
                    snums = self.conf_parser.get(self.program, "chan{}_fbgs".format(i+1)).split(",")
                except configparser.NoOptionError:
                    return
                try:
                    positions = self.conf_parser.get(self.program, "chan{}_positions".format(i+1)).split(",")
                except configparser.NoOptionError:
                    return
            except configparser.NoSectionError:
                reset_config.reset_config(rewrite_program=True)
                return
            if len(snums) != len(positions):
                return
            try:
                positions = helpers.list_cast(positions, int)
                for snum, pos in zip(snums, positions):
                    self.add_fbg(i, snum, pos)
            except ValueError:
                for snum in snums:
                    if snum:
                        self.add_fbg(i, snum)
