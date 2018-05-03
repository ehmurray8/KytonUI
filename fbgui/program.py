"""
Abstract class defines common functionality between calibration
program and baking program.
"""
import abc
import uuid
import configparser
import os
import sqlite3
import tkinter as tk
from tkinter import ttk, messagebox as mbox
from threading import Thread
from fbgui import file_helper as fh, graphing as graphing, dev_helper as dev_helper, ui_helper as ui_helper, \
    options_frame as options_frame
from fbgui.constants import PROG_CONFIG_PATH, CONFIG_IMG_PATH, GRAPH_PATH, FILE_PATH, DB_PATH, DEV_CONFIG_PATH
from fbgui.constants import CAL, BAKING, LASER, SWITCH, TEMP, OVEN
from fbgui.table import Table
import visa
from PIL import ImageTk, Image
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure
from fbgui.graph_toolbar import Toolbar
from fbgui import messages, helpers


class ProgramType(object):
    """Defines constants for each type of program."""

    def __init__(self, prog_id):
        self.prog_id = prog_id
        if self.prog_id == BAKING:
            self.start_title = "Start Baking"
            self.title = "Configure Baking"
            self.plot_num = 230
        else:
            self.start_title = "Start Calibration"
            self.title = "Configure Calibration"
            self.plot_num = 230


class Program(ttk.Notebook):
    """Definition of the abstract program page."""

    def __init__(self, master, program_type):
        style = ttk.Style()
        style.configure('InnerNB.TNotebook', tabposition='wn')
        super().__init__(master.main_notebook, style='InnerNB.TNotebook')

        self.conf_parser = configparser.ConfigParser()
        self.conf_parser.read(PROG_CONFIG_PATH)
        self.master = master
        self.connection_thread = None
        self.program_type = program_type
        self.channels = [[], [], [], []]
        self.switches = [[], [], [], []]
        self.snums = []
        self.start_btn = None
        self.need_oven = False
        self.options = None
        self.table = None
        self.graph_helper = None

        self.config_photo = ImageTk.PhotoImage(Image.open(CONFIG_IMG_PATH))
        self.graph_photo = ImageTk.PhotoImage(Image.open(GRAPH_PATH))
        self.file_photo = ImageTk.PhotoImage(Image.open(FILE_PATH))
        self.setup_tabs()

        is_running = self.program_type.prog_id == BAKING and self.conf_parser.getboolean(BAKING, "running")
        is_running = is_running or self.program_type.prog_id == CAL and self.conf_parser.getboolean(CAL, "running")
        if is_running:
            self.start()

    @abc.abstractmethod
    def program_loop(self, thread_id):
        """Main loop that the program uses to run."""
        return

    def create_excel(self):
        """Creates excel file."""
        Thread(target=fh.create_excel_file, args=(self.options.file_name.get(), self.snums, self.master.main_queue,
                                                  self.program_type.prog_id == CAL)).start()

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
        self.table = Table(table_frame, self.create_excel)
        self.table.setup_headers([])
        self.table.pack(fill="both", expand=True)
        fig = Figure(figsize=(5, 5), dpi=100)
        canvas = FigureCanvasTkAgg(fig, graph_frame)
        canvas.show()
        canvas.get_tk_widget().pack(side=tk.BOTTOM, fill=tk.BOTH, expand=True)
        toolbar = Toolbar(canvas, graph_frame)
        toolbar.update()
        file_name = self.options.file_name
        self.graph_helper = graphing.Graphing(file_name, self.program_type.plot_num, self.program_type.prog_id == CAL,
                                              fig, canvas, toolbar, self.master, self.snums)
        toolbar.set_gh(self.graph_helper)
        canvas._tkcanvas.pack(side=tk.TOP, fill=tk.BOTH, expand=True)

    def is_valid_file(self):
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
                self.master.main_queue.put(messages.Message(messages.MessageType.ERROR, "File Error",
                                                            "Cannot put write file to {}.".format(dirname)))
        return valid

    def check_device_config(self):
        try:
            int(self.master.controller_location.get())
            int(self.master.oven_location.get())
            int(self.master.op_switch_port.get())
            int(self.master.sm125_port.get())
            try:
                if sum(bool(int(x)) for x in self.master.op_switch_address.get().split(".")) != 4:
                    raise TypeError
                if sum(bool(int(x)) for x in self.master.sm125_address.get().split(".")) != 4:
                    raise TypeError
            except (ValueError, TypeError):
                raise TypeError
            return True
        except tk.TclError:
            mbox.showerror("Device Configuration Error",
                           "Please fill in all the device configuration inputs on the home screen before starting.")
        except ValueError:
            mbox.showerror("Device Configuration Error",
                           "Please make sure the temperature controller, oven, and port device inputs on " +
                           "the home screen are integer values.")
        except TypeError:
            mbox.showerror("Device Configuration Error",
                           "Please make sure the optical switch, and sm125 addresses are valid IP addresses on the " +
                           "home screen inputs.")
        return False

    def start(self):
        """Starts the recording process."""
        self.start_btn.configure(state=tk.DISABLED)
        self.start_btn.configure(text="Pause")
        can_start = self.check_device_config() and self.options.check_config()
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
                            if pos.get():
                                self.switches[chan].append(pos.get())

                    if any(len(x) > 1 for x in self.channels) and not sum(len(x) for x in self.switches):
                        mbox.showerror("Configuration Error",
                                       "Program was configured to use the optical switch but no " +
                                       "switch positions were provided.")
                        self.pause_program()
                    elif sum(any(x) for x in self.switches) > 1:
                        mbox.showerror("Configuration Error",
                                       "Can only have one channel configured to use the optical switch.")
                        self.pause_program()
                    elif not helpers.is_unique(helpers.flatten(self.switches)):
                        mbox.showerror("Configuration Error",
                                       "Multiple FBGs are configured to use the same switch position.")
                        self.pause_program()
                    else:
                        self.save_config_info()
                        self.master.running_prog = self.program_type.prog_id
                        ui_helper.lock_widgets(self.options)
                        ui_helper.lock_main_widgets(self.master.device_frame)
                        self.graph_helper.show_subplots()
                        headers = fh.create_headers(self.snums, self.program_type.prog_id == CAL, True)
                        headers.pop(0)
                        self.table.setup_headers(headers, True)
                        Thread(target=self.run_program).start()
                        self.start_btn.configure(state=tk.NORMAL)
                else:
                    self.start_btn.configure(text=self.program_type.start_title)
                    self.start_btn.configure(state=tk.NORMAL)
        else:
            self.start_btn.configure(text=self.program_type.start_title)
            self.start_btn.configure(state=tk.NORMAL)

    def run_program(self):
        thread_id = uuid.uuid4()
        self.master.thread_map[thread_id] = True
        self.master.open_threads.append(thread_id)
        if self.connect_devices(thread_id):
            self.program_loop(thread_id)
            self.disconnect_devices()
        else:
            self.pause_program()

    def disconnect_devices(self):
        if self.master.use_dev:
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

    def connect_devices(self, thread_id):
        self.need_oven = False
        need_switch = False
        self.disconnect_devices()
        self.master.conn_dev(LASER, try_once=True)
        self.master.conn_dev(TEMP, try_once=True)

        if self.master.thread_map[thread_id] and sum(len(switch) for switch in self.switches):
            need_switch = True
            self.master.conn_dev(SWITCH, try_once=True)

        if self.master.thread_map[thread_id] and self.master.use_dev \
                and (self.program_type.prog_id == CAL or self.options.set_temp.get()) and self.master.oven is None:
            self.need_oven = True
            self.master.conn_dev(OVEN, try_once=True)

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
        if self.need_oven:
            self.master.conn_dev(OVEN, try_once=not force_connect, thread_id=thread_id)
            if temp is None:
                temp = self.options.set_temp.get()
            try:
                self.master.oven.set_temp(temp)
            except visa.VisaIOError:
                self.master.main_queue.put(messages.Message(messages.MessageType.WARNING, "Connection Error",
                                                            "Failed to set temperature of oven to {}".format(temp)))
            self.master.oven.heater_off()
            self.master.oven.cooling_off()
            if heat:
                try:
                    self.master.oven.heater_on()
                except visa.VisaIOError:
                    self.master.main_queue.put(messages.Message(messages.MessageType.WARNING, "Connection Error",
                                                                "Failed to turn oven heater on."))
            if cooling:
                try:
                    self.master.oven.cooling_on()
                except visa.VisaIOError:
                    self.master.main_queue.put(messages.Message(messages.MessageType.WARNING, "Connection Error",
                                                                "Failed to turn oven cooling on."))

    def save_config_info(self):
        self.conf_parser.set(self.program_type.prog_id, "num_scans", str(self.options.num_pts.get()))
        self.conf_parser.set(self.program_type.prog_id, "file", str(self.options.file_name.get()))
        last_folder = os.path.dirname(self.options.file_name.get())
        self.conf_parser.set(self.program_type.prog_id, "last_folder", last_folder)
        self.conf_parser.set(self.program_type.prog_id, "running", "true")
        for i, (snums, switches) in enumerate(zip(self.channels, self.switches)):
            self.conf_parser.set(BAKING, "chan{}_fbgs".format(i + 1), ",".join(snums))
            self.conf_parser.set(BAKING, "chan{}_positions".format(i + 1), ",".join(str(x) for x in switches))

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
        else:
            self.conf_parser.set(BAKING, "running", "false")
            self.conf_parser.set(self.program_type.prog_id, "use_cool", str(self.options.cooling.get()))
            self.conf_parser.set(self.program_type.prog_id, "num_temp_readings",
                                 str(self.options.num_temp_readings.get()))
            self.conf_parser.set(self.program_type.prog_id, "temp_interval", str(self.options.temp_interval.get()))
            self.conf_parser.set(self.program_type.prog_id, "drift_rate", str(self.options.drift_rate.get()))
            self.conf_parser.set(self.program_type.prog_id, "num_cycles", str(self.options.num_cal_cycles.get()))
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
        """Pauses the program."""
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

    def get_wave_amp_data(self, thread_id):
        positions_used = [len(x) for x in self.channels]
        return dev_helper.avg_waves_amps(self.master.laser, self.master.switch, self.switches,
                                         self.options.num_pts.get(), positions_used, self.master.use_dev,
                                         sum(len(s) > 0 for s in self.snums), thread_id, self.master.thread_map)
