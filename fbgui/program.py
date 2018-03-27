"""
Abstract class defines common functionality between calibration
program and baking program.
"""

import abc
import configparser
import os
import sqlite3
import threading
import tkinter as tk
from tkinter import ttk, messagebox as mbox

import fbgui.dev_helper as dev_helper
import fbgui.file_helper as fh
import fbgui.graphing as graphing
import fbgui.options_frame as options_frame
import fbgui.ui_helper as ui_helper
from PIL import Image, ImageTk
from fbgui.constants import CAL, BAKING, LASER, SWITCH, TEMP, OVEN
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2TkAgg
from matplotlib.figure import Figure
from fbgui.table import Table

from fbgui import helpers as help


class ProgramType(object):
    """Defines constants for each type of program."""

    def __init__(self, prog_id):
        self.prog_id = prog_id
        if self.prog_id == BAKING:
            self.start_title = "Start Baking"
            self.title = "Configure Baking"
            self.in_prog_msg = "Baking..."
            self.plot_num = 230
            self.num_graphs = 6
        else:
            self.start_title = "Start Calibration"
            self.title = "Configure Calibration"
            self.in_prog_msg = "Calibrating..."
            self.plot_num = 240
            self.num_graphs = 7


class Program(ttk.Notebook):
    """Definition of the abstract program page."""
    __metaclass_ = abc.ABCMeta

    def __init__(self, master, program_type):
        style = ttk.Style()
        style.configure('InnerNB.TNotebook', tabposition='wn')

        super().__init__(master.main_notebook, style='InnerNB.TNotebook')

        self.master = master
        self.program_type = program_type
        self.channels = [[], [], [], []]
        self.switches = [[], [], [], []]
        self.snums = []
        self.stable_count = 0
        self.running = False
        self.cancel_run = False
        self.chan_error_been_warned = False
        self.start_btn = None
        self.delayed_prog = None
        self.table_thread = None

        self.conf_parser = configparser.ConfigParser()
        self.conf_parser.read(os.path.join("config", "prog_config.cfg"))

        self.config_frame = ttk.Frame(self)
        self.graph_frame = ttk.Frame(self)
        table_frame = ttk.Frame(self)

        # Need images as instance variables to prevent garbage collection
        config_path = os.path.join("assets", "config.png")
        graph_path = os.path.join("assets", "graph.png")
        file_path = os.path.join("assets", "file.png")
        img_config = Image.open(config_path)
        img_graph = Image.open(graph_path)
        img_file = Image.open(file_path)

        self.img_config = ImageTk.PhotoImage(img_config)
        self.img_graph = ImageTk.PhotoImage(img_graph)
        self.img_table = ImageTk.PhotoImage(img_file)

        # Set up config tab
        self.add(self.config_frame, image=self.img_config)
        self.options = options_frame.OptionsPanel(self.config_frame, self.program_type.prog_id)
        self.start_btn = self.options.create_start_btn(self.start)
        self.options.init_fbgs()
        self.options.pack(expand=True, side="right", fill="both", padx=50, pady=15)

        # Set up graphing tab
        self.add(self.graph_frame, image=self.img_graph)

        # Set up table tab
        self.add(table_frame, image=self.img_table)
        ttk.Label(table_frame, text="Last 100 Readings").pack(anchor="center")
        self.table = Table(table_frame, self.create_excel)
        self.table.setup_headers([])
        self.table.pack(fill="both", expand=True)

        # Graphs need to be empty until csv is created
        self.fig = Figure(figsize=(5, 5), dpi=100)

        self.canvas = FigureCanvasTkAgg(self.fig, self.graph_frame)
        self.canvas.show()
        is_cal = False
        if self.program_type.prog_id == CAL:
            is_cal = True

        self.canvas.get_tk_widget().pack(side=tk.BOTTOM, fill=tk.BOTH, expand=True)

        self.toolbar = Toolbar(self.canvas, self.graph_frame)
        self.toolbar.update()
        file_name = self.options.file_name
        self.graph_helper = graphing.Graphing(file_name, self.program_type.plot_num, is_cal, self.fig,
                                              self.canvas, self.toolbar, self.master, self.snums)
        self.toolbar.set_gh(self.graph_helper)
        self.canvas._tkcanvas.pack(side=tk.TOP, fill=tk.BOTH, expand=True)

        is_running = self.program_type.prog_id == BAKING and self.conf_parser.getboolean(BAKING, "running")
        is_running = is_running or self.program_type.prog_id == CAL and self.conf_parser.getboolean(CAL, "running")

        if is_running:
            self.start()

    @abc.abstractmethod
    async def program_loop(self):
        """Main loop that the program uses to run."""
        return

    def create_excel(self):
        """Creates excel file."""
        threading.Thread(target=fh.create_excel_file, args=(self.options.file_name.get(), self.snums,
                                                            self.program_type.prog_id == CAL)).start()

    def valid_header(self, csv_file, file_lines):
        saved_snums = help.clean_str_list(next(file_lines).split(","))
        num_conf_fbgs = len(help.flatten(self.options.sn_ents))
        if len(saved_snums) != num_conf_fbgs:
            file_error(csv_file, "contains {} FBGs you are attempting to record data for {} FBGs. "
                                 .format(len(saved_snums), num_conf_fbgs) +
                                 "The file contains the FBGS: {}".format(str(saved_snums)))
            return False
        elif set(saved_snums) != set(x.get() for x in help.flatten(self.options.sn_ents)):
            file_error(csv_file, "has FBGs in it that differ from the ones you have configured the program to record "
                                 "data for. The file contains the FBGs: {}".format(str(saved_snums)))
            return False
        return True

    def is_valid_file(self):
        conn = sqlite3.connect("db/program_data.db")
        cur = conn.cursor()
        name = help.get_file_name(self.options.file_name.get())
        cur.execute("SELECT ID, ProgName, ProgType from map")
        rows = cur.fetchall()
        names = [row[1] for row in rows]
        types = [row[2] for row in rows]
        valid = True
        try:
            idx = names.index(name)
            if types[idx] != self.program_type.prog_id.lower():
                valid = False
        except ValueError:
            pass
        if not os.path.isdir(os.path.split(self.options.file_name.get())[0]):
            try:
                os.mkdir(os.path.split(self.options.file_name.get())[0])
            except FileNotFoundError:
                # File Error cannot make directory
                valid = False
        return valid

    def start(self):
        """Starts the recording process."""
        self.start_btn.configure(text="Pause")
        can_start = self.options.check_config()
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
                else:
                    self.pause_program()
            elif not len(self.options.sn_ents):
                mbox.showerror("Configuration Error",
                               "Please add fbg entries to your configuration before running the program.")
            else:
                if self.is_valid_file():
                    for chan, snum, pos in zip(help.flatten(self.options.chan_nums), help.flatten(self.options.sn_ents),
                                               help.flatten(self.options.switch_positions)):
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
                    elif not help.is_unique(help.flatten(self.switches)):
                        mbox.showerror("Configuration Error",
                                       "Multiple FBGs are configured to use the same switch position.")
                        self.pause_program()
                    else:
                        self.save_config_info()
                        self.master.running_prog = self.program_type.prog_id
                        ui_helper.lock_widgets(self.options)
                        self.graph_helper.show_subplots()
                        headers = fh.create_headers(self.snums, self.program_type.prog_id == CAL, True)
                        headers.pop(0)
                        self.table.setup_headers(headers, True)
                        self.program_start()
                else:
                    self.pause_program()
        else:
            self.pause_program()

    def program_start(self):
        threading.Thread(target=self.connect_devices).start()

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

    def connect_devices(self):
        need_oven = False
        need_switch = False
        self.disconnect_devices()
        self.master.conn_buttons[LASER]()
        self.master.conn_buttons[TEMP]()
        if sum(len(switch) for switch in self.switches):
            need_switch = True
            self.master.conn_buttons[SWITCH]()
        if self.master.use_dev and (self.program_type.prog_id == CAL or self.options.set_temp.get()) \
                and self.master.oven is None:
            need_oven = True
            self.master.conn_buttons[OVEN]()
        if need_oven and self.master.oven is not None and self.program_type.prog_id == BAKING:
            self.master.loop.run_until_complete(self.set_oven_temp())
        if need_oven == (self.master.oven is not None) and (self.master.switch is not None) == need_switch and \
                self.master.laser is not None and self.master.temp_controller is not None:
            self.disconnect_devices()
            self.master.running = True
            self.program_loop()
        else:
            self.disconnect_devices()
            self.pause_program()

    async def set_oven_temp(self):
        await self.master.oven.set_temp(self.options.set_temp.get())
        await self.master.oven.heater_on()

    def save_config_info(self):
        self.conf_parser.set(self.program_type.prog_id, "num_scans", str(self.options.num_pts.get()))
        self.conf_parser.set(self.program_type.prog_id, "file", str(self.options.file_name.get()))
        last_folder = os.path.dirname(self.options.file_name.get())
        self.conf_parser.set(self.program_type.prog_id, "last_folder", last_folder)
        self.conf_parser.set(self.program_type.prog_id, "running", "true")
        for i, (snums, switches) in enumerate(zip(self.channels, self.switches)):
            self.conf_parser.set(BAKING, "chan{}_fbgs".format(i+1), ",".join(snums))
            self.conf_parser.set(BAKING, "chan{}_positions".format(i+1), ",".join(str(x) for x in switches))

        if self.program_type.prog_id == BAKING:
            self.conf_parser.set(CAL, "running", "false")
            self.conf_parser.set(self.program_type.prog_id, "set_temp", str(self.options.set_temp.get()))
            self.conf_parser.set(self.program_type.prog_id, "drift_rate", str(self.options.drift_rate.get()))
            self.conf_parser.set(self.program_type.prog_id, "prim_interval", str(self.options.prim_time.get()))
        else:
            self.conf_parser.set(BAKING, "running", "false")
            self.conf_parser.set(self.program_type.prog_id, "use_cool", str(self.options.cooling.get()))
            self.conf_parser.set(self.program_type.prog_id, "num_temp_readings", str(self.options.num_temp_readings.get()))
            self.conf_parser.set(self.program_type.prog_id, "temp_interval", str(self.options.temp_interval.get()))
            self.conf_parser.set(self.program_type.prog_id, "drift_rate", str(self.options.drift_rate.get()))
            self.conf_parser.set(self.program_type.prog_id, "num_cycles", str(self.options.num_cal_cycles.get()))
            self.conf_parser.set(self.program_type.prog_id, "target_temps", ",".join(str(x) for x in self.options.get_target_temps()))

        with open(os.path.join("config", "prog_config.cfg"), "w") as pcfg:
            self.conf_parser.write(pcfg)

    def pause_program(self):
        """Pauses the program."""
        self.start_btn.configure(text=self.program_type.start_title)
        ui_helper.unlock_widgets(self.options)
        self.master.running = False
        self.master.running_prog = None
        self.conf_parser.set(BAKING, "running", "false")
        self.conf_parser.set(CAL, "running", "false")
        with open(os.path.join("config", "prog_config.cfg"), "w") as pcfg:
            self.conf_parser.write(pcfg)
        self.stable_count = 0
        self.snums = []
        self.channels = [[], [], [], []]
        self.switches = [[], [], [], []]

    async def get_wave_amp_data(self):
        positions_used = [len(x) for x in self.channels]
        return await dev_helper.avg_waves_amps(self.master.laser, self.master.switch, self.switches,
                                               self.options.num_pts.get(), positions_used, self.master.use_dev,
                                               sum(len(s) > 0 for s in self.snums))


class Toolbar(NavigationToolbar2TkAgg):
    """Overrides the default Matplotlib toolbar to add play and pause animation buttons."""
    def __init__(self, figure_canvas, parent):
        self.toolitems = (('Home', 'Reset original view', 'home', 'home'),
                              ('Back', 'Back to  previous view', 'back', 'back'),
                              ('Forward', 'Forward to next view',
                               'forward', 'forward'),
                              (None, None, None, None),
                              ('Pan', 'Pan axes with left mouse, zoom with right',
                               'move', 'pan'),
                              ('Zoom', 'Zoom to rectangle', 'zoom_to_rect', 'zoom'),
                              (None, None, None, None),
                              ('Subplots', 'Configure subplots',
                               'subplots', 'configure_subplots'),
                              ('Save', 'Save the figure',
                               'filesave', 'save_figure'),
                              (None, None, None, None),
                              ('Pause', 'Pause the animation', 'pause', 'pause'),
                              ('Play', 'Play the animation', 'play', 'play'))

        self.figure_canvas = figure_canvas
        self.parent = parent
        self.graphing_helper = None
        super().__init__(self.figure_canvas, self.parent)

    def set_gh(self, graphing_helper):
        """Sets the graphing helper."""
        self.graphing_helper = graphing_helper

    def play(self):
        """Plays graph animation linked to play button on toolbar."""
        self.graphing_helper.play()

    def pause(self):
        """Pauses graph animation linked to button on toolbar."""
        self.graphing_helper.pause()


def file_error(csv_file, extra_info):
        mbox.showerror("File Error", "The file {} cannot be used as the file for this program, this file "
                                       .format(csv_file) + extra_info)
