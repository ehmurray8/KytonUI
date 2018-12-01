"""
Abstract class defines common functionality between calibration program and baking program.
"""
import abc
import configparser
import os
import re
import socket
import sqlite3
import tkinter as tk
import time
import uuid
from threading import Thread
from tkinter import ttk, messagebox as mbox
from typing import List, Tuple

import visa
from PIL import ImageTk, Image
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure

from fbgui import graphing, ui_helper, options_frame, helpers
from fbgui.constants import PROG_CONFIG_PATH, CONFIG_IMG_PATH, GRAPH_PATH, FILE_PATH, DB_PATH, DEV_CONFIG_PATH, \
    CAL, BAKING, LASER, SWITCH, TEMP, OVEN, REAL_POINT_HEADER, TEMPERATURE_HEADER
from fbgui.database_controller import DatabaseController
from fbgui.datatable import DataTable
from fbgui.excel_file_controller import ExcelFileController
from fbgui.exceptions import ProgramStopped
from fbgui.graph_toolbar import Toolbar
from fbgui.laser_recorder import LaserRecorder
from fbgui.main_program import Application
from fbgui.messages import MessageType, Message

MPL_PLOT_NUM = 230


class ProgramType(object):
    """
    Defines constants for calibration and baking programs.

    :ivar str start_title: Title of the start button when the program is paused on the options screen
    :ivar str title: Title of the program options screen
    """

    def __init__(self, prog_id: str):
        """
        Sets up the program constants.

        :param prog_id: program identifier string
        """
        self.prog_id = prog_id
        if self.prog_id == BAKING:
            self.start_title = "Start Baking"
            self.title = "Configure Baking"
        else:
            self.start_title = "Start Calibration"
            self.title = "Configure Calibration"


class Program(ttk.Notebook):
    """
    Definition of the abstract program page, contains shared logic between the two program types, and implements
    the ttk Notebook widget.

    :ivar configparser.ConfigParser conf_parser: ConfigParser used for reading the prog_config file
    :ivar List[List[str]] channels: 2D list one list for each SM125 channel, each element is a serial number, and is
                                    the same shape as the FBG inputs on the options screen
    :ivar List[List[int]] switches: 2D list one list for each SM125 channel, each element is a switch position,
                                    same shape as the channels matrix
    :ivar List[str] snums: serial numbers in order as a flatten list of the channels matrix
    :ivar ttk.Button start_btn: start button on the options screen
    :ivar bool need_oven: True if the program needs to use the oven, False otherwise
    :ivar options_frame.OptionsPanel options: options screen wrapper
    :ivar DataTable table: data table screen wrapper
    :ivar graphing.Graphing graph_helper: graphing screen wrapper
    """

    def __init__(self, master: Application, program_type: ProgramType):
        """
        Sets up the program UI, and data structures.

        :param master: master Application program
        :param program_type: type of program that is being created
        """
        style = ttk.Style()
        style.configure('InnerNB.TNotebook', tabposition='wn')
        super().__init__(master.main_notebook, style='InnerNB.TNotebook')

        self.conf_parser = configparser.ConfigParser()
        self.conf_parser.read(PROG_CONFIG_PATH)
        self.master = master
        self.program_type = program_type
        self.channels = [[], [], [], []]  # type: List[List[str]]
        self.switches = [[], [], [], []]  # type: List[List[int]]
        self.snums = []  # type: List[str]
        self.start_btn = None  # type: ttk.Button
        self.need_oven = False
        self.options = None  # type: options_frame.OptionsPanel
        self.table = None  # type: DataTable
        self.graph_helper = None  # type: graphing.Graphing
        self.database_controller = None  # type: DatabaseController

        # Needed to avoid garbage collection
        self.config_photo = ImageTk.PhotoImage(Image.open(CONFIG_IMG_PATH))
        self.graph_photo = ImageTk.PhotoImage(Image.open(GRAPH_PATH))
        self.file_photo = ImageTk.PhotoImage(Image.open(FILE_PATH))
        self.setup_tabs()

        is_running = self.program_type.prog_id == BAKING and self.conf_parser.getboolean(BAKING, "running")
        is_running = is_running or self.program_type.prog_id == CAL and self.conf_parser.getboolean(CAL, "running")
        if is_running:
            self.start()

    @abc.abstractmethod
    def program_loop(self, thread_id: uuid.UUID):
        """
        Main loop that the program uses to run.

        :param thread_id: UUID of the thread running the program loop
        """
        return

    def create_excel(self):
        """Creates excel file, in a new thread."""
        bake_sensitivity = self.options.bake_sensitivity.get()
        if bake_sensitivity == 0:
            bake_sensitivity = None
        excel_controller = ExcelFileController(self.options.file_name.get(), self.snums,
                                               self.master.main_queue, self.program_type.prog_id, bake_sensitivity)
        Thread(target=excel_controller.create_excel).start()

    def setup_tabs(self):
        """Setup the configuration, graphing, and table tabs."""
        config_frame = ttk.Frame(self)
        graph_frame = ttk.Frame(self)
        table_frame = ttk.Frame(self)

        # Set up config tab
        self.add(config_frame, image=self.config_photo)
        self.options = options_frame.OptionsPanel(config_frame, self.program_type.prog_id)
        self.start_btn = self.options.create_start_btn(self.start)
        self.options.init_fbgs()
        self.options.pack(expand=True, side="right", fill="both", padx=50, pady=15)

        # Set up graphing tab
        self.add(graph_frame, image=self.graph_photo)

        # Set up table tab
        self.add(table_frame, image=self.file_photo)
        ttk.Label(table_frame, text="Last 100 Readings").pack(anchor="center")
        self.table = DataTable(table_frame, self.create_excel, self.master.main_queue)
        self.table.setup_headers([])
        self.table.pack(fill="both", expand=True)
        fig = Figure(figsize=(5, 5), dpi=100)
        canvas = FigureCanvasTkAgg(fig, graph_frame)
        canvas.show()
        canvas.get_tk_widget().pack(side=tk.BOTTOM, fill=tk.BOTH, expand=True)
        toolbar = Toolbar(canvas, graph_frame)
        toolbar.update()
        file_name = self.options.file_name
        self.database_controller = DatabaseController(file_name.get(), self.snums,
                                                      self.master.main_queue, self.program_type.prog_id,
                                                      self.table, excel_table=self.master.excel_table)
        self.graph_helper = graphing.Graphing(MPL_PLOT_NUM, self.program_type.prog_id == CAL,
                                              fig, canvas, toolbar, self.master, self.snums, self.master.main_queue,
                                              self.database_controller)
        toolbar.set_gh(self.graph_helper)

        # noinspection PyProtectedMember
        canvas._tkcanvas.pack(side=tk.TOP, fill=tk.BOTH, expand=True)

    def is_valid_file(self) -> bool:
        """
        Checks if the file is valid, either there is an entry for the program name in the map table of the same type,
        or the file can be created at the specified location.

        :return: True if the file is valid, False otherwise
        """
        valid = True
        conn = sqlite3.connect(DB_PATH)
        cur = conn.cursor()
        name = helpers.get_file_name(self.options.file_name.get())
        try:
            cur.execute("SELECT ID, ProgName, ProgType from map")
            rows = cur.fetchall()
            names = [row[1] for row in rows]
            types = [row[2] for row in rows]
            idx = names.index(name)
            if types[idx] != self.program_type.prog_id.lower():
                valid = False
        except ValueError:
            pass
        except sqlite3.OperationalError:
            pass

        if not os.path.isdir(os.path.split(self.options.file_name.get())[0]):
            dirname = os.path.split(self.options.file_name.get())[0]
            try:
                os.mkdir(dirname)
            except FileNotFoundError:
                valid = False
                self.master.main_queue.put(Message(MessageType.ERROR, "File Error",
                                                   "Cannot put write file to {}.".format(dirname)))
        return valid

    def check_device_config(self) -> bool:
        """
        Checks if the device configuration is valid on the home screen. The IP addresses are correctly
        formatted, and the ports are integer values.

        :return: True if the home screen device inputs are properly configured, False otherwise
        """
        device_config_title = "Device Configuration Error"
        proper_config = True
        try:
            gpib_re = re.compile(r"GPIB\d+::\d+::INSTR$")
            ip_re = re.compile(r"\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}")

            ip_error_message = "Please make sure the {} address input on the home screen is a valid IP address."
            gpib_error_message = "Please make sure the {} input on the home screen "\
                                 "is a valid GPIB address. (eg. GPIB0::12::INSTR)"
            port_error_message = "Please make sure the {} port input on the home screen is an integer value."

            if not gpib_re.match(self.master.controller_location.get()):
                proper_config = False
                mbox.showerror(device_config_title, gpib_error_message.format("temperature controller"))
            if not gpib_re.match(self.master.oven_location.get()):
                proper_config = False
                mbox.showerror(device_config_title, gpib_error_message.format("oven"))
            if not ip_re.match(self.master.sm125_address.get()):
                proper_config = False
                mbox.showerror(device_config_title, ip_error_message.format("sm125"))
            if not ip_re.match(self.master.op_switch_address.get()):
                proper_config = False
                mbox.showerror(device_config_title, ip_error_message.format("optical switch"))

            try:
                int(self.master.op_switch_port.get())
            except ValueError:
                proper_config = False
                mbox.showerror(device_config_title, port_error_message.format("optical switch"))
            try:
                int(self.master.sm125_port.get())
            except ValueError:
                proper_config = False
                mbox.showerror(device_config_title, port_error_message.format("sm125"))
        except tk.TclError:
            mbox.showerror(device_config_title,
                           "Please fill in all the device configuration inputs on the home screen before starting.")
            proper_config = False
        return proper_config

    def start(self):
        """
        Checks to make sure all the settings are properly configured, and then runs the program if they are.
        Pause the program if the program is already running.
        """
        self.start_btn.configure(state=tk.DISABLED)
        self.start_btn.configure(text="Pause")

        controller = self.database_controller.new_instance(self.options.file_name.get(), self.snums)
        can_start = self.check_device_config() and self.options.check_config(controller)
        if can_start:
            if self.master.running:
                if self.master.running_prog != self.program_type.prog_id:
                    prog = "Baking"
                    run = "calibration"
                    if self.program_type.prog_id == BAKING:
                        prog = "Calibration"
                        run = "bake"
                    mbox.showerror("{} program is already running".format(prog),
                                   "Please stop the {} program before starting the {}."
                                   .format(prog, run))
                    self.start_btn.configure(text=self.program_type.start_title)
                else:
                    self.pause_program()
            elif not len(self.options.sn_ents):
                mbox.showerror("Configuration Error",
                               "Please add fbg entries to your configuration before running the program.")
            else:
                if self.is_valid_file():
                    for chan, snum, pos in zip(helpers.flatten(self.options.chan_nums),
                                               helpers.flatten(self.options.sn_ents),
                                               helpers.flatten(self.options.switch_positions)):
                        if snum.get() and snum.get() not in self.snums:
                            self.snums.append(snum.get())
                            self.channels[chan].append(snum.get())
                            self.switches[chan].append(pos.get())

                    self.save_config_info()
                    self.master.running_prog = self.program_type.prog_id
                    ui_helper.lock_widgets(self.options)
                    ui_helper.lock_main_widgets(self.master.device_frame)
                    self.graph_helper.show_subplots()
                    self.database_controller.reset_controller(self.options.file_name.get(), self.snums)

                    self.handle_partial_cycles()
                    Thread(target=self.run_program).start()
                    self.start_btn.configure(state=tk.NORMAL)
                else:
                    self.start_btn.configure(text=self.program_type.start_title)
                    self.start_btn.configure(state=tk.NORMAL)
        else:
            self.start_btn.configure(text=self.program_type.start_title)
            self.start_btn.configure(state=tk.NORMAL)

    def handle_partial_cycles(self):
        if self.program_type.prog_id == CAL:
            try:
                data_frame = self.database_controller.to_data_frame()
            except IndexError:
                return
            real_point_data_frame = data_frame[data_frame[REAL_POINT_HEADER] == "True"]
            cycle_nums = set(self.database_controller.get_cycle_nums())
            partial_cycle_nums = []
            num_points_in_cycle = len(self.options.get_target_temps())
            for temperature, _, _ in self.options.extra_points:
                if temperature.get() != 0:
                    num_points_in_cycle += 1
            for cycle_num in cycle_nums:
                temperatures = list(
                    real_point_data_frame[real_point_data_frame["Cycle Num"] == cycle_num][TEMPERATURE_HEADER])
                if len(temperatures) != num_points_in_cycle:
                    partial_cycle_nums.append(cycle_num)

            if len(partial_cycle_nums) and mbox.askyesno("Calibration", "The run contains partially completed cycles, "
                                                                        "would you like to delete them?"):
                self.database_controller.delete_partial_cycles(partial_cycle_nums)

    def run_program(self):
        """Setups the thread and the thread map, and then starts the data collection process."""
        thread_id = uuid.uuid4()
        self.master.thread_map[thread_id] = True
        self.master.open_threads.append(thread_id)
        self.master.main_queue.put(Message(MessageType.INFO, text="Starting data collection for {} program."
                                           .format(self.program_type.prog_id), title=None))
        start_time = time.time()
        if self.connect_devices(thread_id):
            try:
                self.program_loop(thread_id)
            except ProgramStopped:
                pass
        self.pause_program()
        end_time = time.time()
        elapsed_time = round((end_time - start_time) / 60, 1)
        self.master.main_queue.put(Message(MessageType.INFO, text="{} program is finished. It ran for {} minutes."
                                           .format(self.program_type.prog_id, elapsed_time), title=None))

    def disconnect_devices(self):
        """Disconnect all the devices, and set them to None."""
        if self.master.oven is not None:
            self.master.oven.close()
            self.master.oven = None
        if self.master.laser is not None:
            self.master.laser.close()
            self.master.laser = None
        if self.master.temp_controller is not None:
            self.master.temp_controller.close()
            self.master.temp_controller = None
        if self.master.switch is not None:
            self.master.switch.close()
            self.master.switch = None

    def connect_devices(self, thread_id: uuid.UUID) -> bool:
        """
        Connect to all the required devices, as configured on the main screen.

        :param thread_id: the thread the code is currently running in
        :return: True if all the devices can be connected to, False otherwise
        """
        self.need_oven = False
        need_switch = False
        self.disconnect_devices()
        self.master.conn_dev(LASER, try_once=True)
        self.master.conn_dev(TEMP, try_once=True)

        if self.master.thread_map[thread_id] and sum(len(switch) for switch in self.switches):
            need_switch = True
            self.master.conn_dev(SWITCH, try_once=True)

        try:
            if self.master.thread_map[thread_id] \
                    and (self.program_type.prog_id == CAL or self.options.set_temp.get()) and self.master.oven is None:
                self.need_oven = True
                self.master.conn_dev(OVEN, try_once=True)
        except tk.TclError:
            self.need_oven = False

        if self.master.thread_map[thread_id] and self.need_oven and self.master.oven is not None \
                and self.program_type.prog_id == BAKING:
            self.set_oven_temp(force_connect=True, thread_id=thread_id)

        if self.master.thread_map[thread_id] and self.need_oven == (self.master.oven is not None) and\
                (self.master.switch is not None) == need_switch and self.master.laser is not None and \
                self.master.temp_controller is not None:
            self.disconnect_devices()
            self.master.running = True
            return True
        return False

    def set_oven_temp(self, temp: float=None, heat: bool=True, force_connect: bool=False, thread_id=None,
                      cooling=False):
        """
        Sets the oven temperature to temp, or to the bake temperature configured on the options screen.

        :param temp: temp to set the oven to, if None use the baking temperature on the options screen
        :param heat: If True turn on the heater
        :param force_connect: If True make sure the device is connected to, otherwise only try to connect to the
                              device once
        :param thread_id: UUID of the thread the code is currently running in
        :param cooling: If True turn on the oven cooling
        """
        temp_set = False
        while not temp_set:
            if temp is None and self.need_oven:
                temp = self.options.set_temp.get()
            try:
                if self.need_oven:
                    self.master.conn_dev(OVEN, try_once=not force_connect, thread_id=thread_id)
                    try:
                        self.master.oven.set_temp(temp)
                    except visa.VisaIOError:
                        self.master.main_queue.put(Message(MessageType.WARNING, "Connection Issue",
                                                           "Failed to set temperature of oven to {}".format(temp)))
                    try:
                        self.master.oven.heater_off()
                        self.master.oven.cooling_off()
                    except visa.VisaIOError:
                        self.master.main_queue.put(Message(MessageType.WARNING, "Connection Issue",
                                                           "Failed to turn off oven cooling and heating."))

                    if heat and not cooling:
                        try:
                            self.master.oven.heater_on()
                        except visa.VisaIOError:
                            self.master.main_queue.put(Message(MessageType.WARNING, "Connection Issue",
                                                               "Failed to turn oven heater on."))
                    if cooling and self.options.cooling.get():
                        try:
                            self.master.oven.cooling_on()
                        except visa.VisaIOError:
                            self.master.main_queue.put(Message(MessageType.WARNING, "Connection Issue",
                                                               "Failed to turn oven cooling on."))
                temp_set = True
            except (AttributeError, visa.VisaIOError):
                if not force_connect:
                    self.master.main_queue.put(Message(MessageType.WARNING, "Device Connection Issue",
                                                       "Failed to set the oven temperature to {} C. Trying to set the "
                                                       "temperature again.".format(temp)))
                else:
                    self.master.main_queue.put(Message(MessageType.WARNING, "Device Connection Issue",
                                                       "Failed to set the oven temperature to {} C.".format(temp)))

    def save_config_info(self):
        """Write the options, and devices configuration to the prog_config and devices config respectively."""
        self.conf_parser.set(self.program_type.prog_id, "num_scans", str(self.options.num_pts.get()))
        self.conf_parser.set(self.program_type.prog_id, "file", str(self.options.file_name.get()))
        last_folder = os.path.dirname(self.options.file_name.get())
        self.conf_parser.set(self.program_type.prog_id, "last_folder", last_folder)
        self.conf_parser.set(self.program_type.prog_id, "running", "true")
        for i, (snums, switches) in enumerate(zip(self.channels, self.switches)):
            self.conf_parser.set(self.program_type.prog_id, "chan{}_fbgs".format(i + 1), ",".join(snums))
            self.conf_parser.set(self.program_type.prog_id, "chan{}_positions".format(i + 1),
                                 ",".join(str(x) for x in switches))

        if self.program_type.prog_id == BAKING:
            self.conf_parser.set(CAL, "running", "false")
            try:
                self.conf_parser.set(self.program_type.prog_id, "set_temp", str(self.options.set_temp.get()))
            except tk.TclError:
                pass
            try:
                self.conf_parser.set(self.program_type.prog_id, "drift_rate", str(self.options.drift_rate.get()))
            except tk.TclError:
                pass
            self.conf_parser.set(self.program_type.prog_id, "prim_interval", str(self.options.prim_time.get()))
            self.conf_parser.set(self.program_type.prog_id, "bake_sensitivity", str(self.options.bake_sensitivity.get()))
        else:
            self.conf_parser.set(BAKING, "running", "false")
            self.conf_parser.set(self.program_type.prog_id, "use_cool", str(self.options.cooling.get()))
            self.conf_parser.set(self.program_type.prog_id, "num_temp_readings",
                                 str(self.options.num_temp_readings.get()))
            self.conf_parser.set(self.program_type.prog_id, "temp_interval", str(self.options.temp_interval.get()))
            self.conf_parser.set(self.program_type.prog_id, "drift_rate", str(self.options.drift_rate.get()))
            self.conf_parser.set(self.program_type.prog_id, "num_cycles", str(self.options.num_cal_cycles.get()))
            for i, (temperature, wavelength_text, power_text) in enumerate(self.options.extra_points):
                self.conf_parser.set(self.program_type.prog_id, "extra_point{}_temperature".format(i+1),
                                     str(temperature.get()))
                self.conf_parser.set(self.program_type.prog_id, "extra_point{}_wavelengths".format(i+1),
                                     wavelength_text.get(1.0, tk.END))
                self.conf_parser.set(self.program_type.prog_id, "extra_point{}_powers".format(i+1),
                                     power_text.get(1.0, tk.END))
            self.conf_parser.set(self.program_type.prog_id, "target_temps",
                                 ",".join(str(x) for x in self.options.get_target_temps()))

        with open(PROG_CONFIG_PATH, "w") as pcfg:
            self.conf_parser.write(pcfg)

        dev_conf = configparser.ConfigParser()
        dev_conf.read(DEV_CONFIG_PATH)

        dev_conf.set("Devices", "oven_location", str(self.master.oven_location.get()))
        dev_conf.set("Devices", "controller_location", str(self.master.controller_location.get()))
        dev_conf.set("Devices", "op_switch_address", str(self.master.op_switch_address.get()))
        dev_conf.set("Devices", "op_switch_port", str(self.master.op_switch_port.get()))
        dev_conf.set("Devices", "sm125_port", str(self.master.sm125_port.get()))
        dev_conf.set("Devices", "sm125_address", str(self.master.sm125_address.get()))

        with open(DEV_CONFIG_PATH, "w") as dcfg:
            dev_conf.write(dcfg)

    def pause_program(self):
        """Pauses the program, and stops the running thread."""
        self.disconnect_devices()
        for tid in self.master.open_threads:
            self.master.thread_map[tid] = False
        self.master.open_threads.clear()
        self.start_btn.configure(text=self.program_type.start_title)
        self.start_btn.configure(state=tk.NORMAL)
        ui_helper.unlock_widgets(self.options)
        ui_helper.unlock_main_widgets(self.master.device_frame)
        self.master.running = False
        self.master.running_prog = None
        self.conf_parser.set(BAKING, "running", "false")
        self.conf_parser.set(CAL, "running", "false")
        with open(PROG_CONFIG_PATH, "w") as pcfg:
            self.conf_parser.write(pcfg)
        self.snums = []
        self.channels = [[], [], [], []]
        self.switches = [[], [], [], []]

    def temp_controller_error(self):
        """Writes a temperature controller warning message to the queue log."""
        self.master.main_queue.put(Message(MessageType.WARNING, "Device Connection Issue",
                                           "Failed to collect power and wavelength data from the laser and the "
                                           "switch. Trying to collect data again."))

    def get_wave_amp_data(self, thread_id: uuid.UUID) -> Tuple[List[float], List[float]]:
        """
        Use the dev_helper module to get the wavelength and power data from the SM125.

        :param thread_id: UUID of the thread the code is currently running in
        :return: wavelength readings, power readings
        """
        while True:
            try:
                if sum(len(switch) for switch in self.switches):
                    self.master.conn_dev(SWITCH, thread_id=thread_id)
                self.master.conn_dev(LASER, thread_id=thread_id)
                return LaserRecorder(self.master.laser, self.master.switch, self.switches, self.options.num_pts.get(),
                                     thread_id, self.master.thread_map, self.master.main_queue)\
                    .get_wavelength_amplitude_data()
            except (AttributeError, visa.VisaIOError, socket.error):
                self.temp_controller_error()
