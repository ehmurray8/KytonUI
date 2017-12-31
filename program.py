"""
Abstract class defines common functionality between calibration
program and baking program.
"""

# pylint: disable=import-error, relative-import, protected-access, superfluous-parens
import asyncio
import os
import threading
import abc
from tkinter import ttk, messagebox as mbox
import configparser
from PIL import Image, ImageTk
import tkinter as tk
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2TkAgg
from matplotlib.figure import Figure
import options_frame
import file_helper as fh
import dev_helper
import graphing
import ui_helper
import helpers as help
from constants import CAL, BAKING
from table import Table


class ProgramType(object):  # pylint:disable=too-few-public-methods
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


class Program(ttk.Notebook):  # pylint: disable=too-many-instance-attributes
    """Definition of the abstract program page."""
    __metaclass_ = abc.ABCMeta

    def __init__(self, master, program_type):
        style = ttk.Style()
        style.configure('InnerNB.TNotebook', tabposition='wn')

        super().__init__(style='InnerNB.TNotebook')  # pylint: disable=missing-super-argument

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

        self.conf_parser = configparser.ConfigParser()
        self.conf_parser.read(os.path.join("config", "prog_config.cfg"))

        self.config_frame = ttk.Frame()
        self.graph_frame = ttk.Frame()
        table_frame = ttk.Frame()

        # Need images as instance variables to prevent garbage collection
        config_path = os.path.join("assets", "config.png")
        graph_path = os.path.join("assets", "graph.png")
        table_path = os.path.join("assets", "table.png")
        img_config = Image.open(config_path)
        img_graph = Image.open(graph_path)
        img_table = Image.open(table_path)

        self.img_config = ImageTk.PhotoImage(img_config)
        self.img_graph = ImageTk.PhotoImage(img_graph)
        self.img_table = ImageTk.PhotoImage(img_table)

        # Set up config tab
        self.add(self.config_frame, image=self.img_config)
        self.options = options_frame.OptionsPanel(self.config_frame, self.program_type.prog_id)
        self.start_btn = self.options.create_start_btn(self.start)
        self.options.init_fbgs()
        self.options.grid_rowconfigure(1, minsize=20)
        self.options.grid_rowconfigure(3, minsize=20)
        self.options.grid_rowconfigure(5, minsize=20)
        self.options.pack(expand=True, side="right", fill="both")

        # Set up graphing tab
        self.add(self.graph_frame, image=self.img_graph)

        # Set up table tab
        self.add(table_frame, image=self.img_table)
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
                                              self.canvas, self.toolbar, self.master)
        self.toolbar.set_gh(self.graph_helper)
        self.canvas._tkcanvas.pack(side=tk.TOP, fill=tk.BOTH, expand=True)

        is_running = self.program_type.prog_id == BAKING and self.conf_parser.getboolean(BAKING, "running")
        is_running = is_running or self.program_type.prog_id == CAL and self.conf_parser.getboolean(CAL, "running")

        self.update_table()
        if is_running:
            self.start()

    @abc.abstractmethod
    async def program_loop(self):
        """Main loop that the program uses to run."""
        return

    def update_table(self):
        new_loop = asyncio.new_event_loop()
        t = threading.Thread(target=fh.update_table, args=(self.table, self.options.file_name.get(),
                                                           self.program_type.prog_id == CAL, new_loop))
        t.start()

    def create_excel(self):
        """Creates excel file."""
        fh.create_excel_file(self.options.file_name.get())

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

        if not fh.check_metadata(file_lines, self.program_type.prog_id == CAL, num_conf_fbgs):
            file_error(csv_file, "has been corrupted.")
            return False
        return True

    def is_valid_file(self):
        valid_file = True
        csv_file = help.to_ext(self.options.file_name.get(), "csv")
        if os.path.exists(csv_file):
            file_lines = (line for line in open(csv_file))
            prog_header = next(file_lines)
            if "Metadata" in prog_header:
                if self.program_type.prog_id != BAKING:
                    file_error(csv_file, "was created to be used for baking.")
                    valid_file = False
                else:
                    valid_file = self.valid_header(csv_file, file_lines) and valid_file
            elif "Caldata" in prog_header:
                if self.program_type.prog_id == BAKING:
                    file_error(csv_file, "was created to be used for calibration.")
                    valid_file = False
                else:
                    valid_file = self.valid_header(csv_file, file_lines) and valid_file
            else:
                file_error(csv_file, "already exists and it was not created by this program.")
                valid_file = False
        return valid_file

    def start(self):
        """Starts the recording process."""
        self.update_table()
        self.start_btn.configure(text="Pause")
        can_start = self.options.check_config()
        if can_start:
            if self.delayed_prog is not None:
                    self.master.after_cancel(self.delayed_prog)
                    self.delayed_prog = None
                    self.pause_program()
            elif self.master.running:
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
                mbox.showerror("Invalid configuration",
                               "Please add fbg entries to your configuration before running the program.")
            else:
                if self.is_valid_file():
                    switch_chan = 0
                    for chan, snum, pos in zip(help.flatten(self.options.chan_nums), help.flatten(self.options.sn_ents),
                                               help.flatten(self.options.switch_positions)):
                        if snum.get() and snum.get() not in self.snums:
                            self.snums.append(snum.get())
                            self.channels[chan].append(snum.get())
                            if pos.get():
                                self.switches[chan].append(pos.get())
                                switch_chan = chan + 1

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
                    else:
                        need_switch = False
                        need_oven = False
                        if self.master.laser is None:
                            self.master.conn_buttons[0].invoke()
                        if switch_chan != -1 and self.master.switch is None:
                            need_switch = True
                            self.master.conn_buttons[1].invoke()
                        if self.master.temp_controller is None:
                            self.master.conn_buttons[2].invoke()
                        if (self.program_type.prog_id == CAL or self.options.set_temp.get()) \
                                and self.master.oven is None:
                            need_oven = True
                            self.master.conn_buttons[3].invoke()

                        if self.master.laser is not None and (self.master.switch is not None or not need_switch) and \
                                self.master.temp_controller is not None and (self.master.oven is not None or not need_oven):
                            self.save_config_info()
                            if need_oven and self.program_type.prog_id == BAKING:
                                self.master.oven.set_temp(self.options.set_temp.get())
                                self.master.oven.heater_on()
                            self.master.running = True
                            self.master.running_prog = self.program_type.prog_id
                            # self.header.configure(text=self.program_type.in_prog_msg)
                            ui_helper.lock_widgets(self.options)
                            self.graph_helper.show_subplots()
                            self.delayed_prog = self.master.after(int(self.options.delay.get() * 1000 * 60 * 60 + 1.5),
                                                                  self.run_program)
                        else:
                            self.pause_program()
                else:
                    self.pause_program()

    def run_program(self):
        loop = asyncio.get_event_loop()
        loop.run_until_complete(self.program_loop())
        loop.close()

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
            self.conf_parser.set(self.program_type.prog_id, "init_delay", str(self.options.delay.get()))
            self.conf_parser.set(self.program_type.prog_id, "init_interval", str(self.options.init_time.get()))
            self.conf_parser.set(self.program_type.prog_id, "init_duration", str(self.options.init_duration.get()))
            self.conf_parser.set(self.program_type.prog_id, "prim_interval", str(self.options.prim_time.get()))
        else:
            self.conf_parser.set(BAKING, "running", "false")
            self.conf_parser.set(self.program_type.prog_id, "use_cool", str(self.options.cooling.get()))
            self.conf_parser.set(self.program_type.prog_id, "num_temp_readings", str(self.options.num_temp_readings.get()))
            self.conf_parser.set(self.program_type.prog_id, "temp_interval", str(self.options.temp_interval.get()))
            self.conf_parser.set(self.program_type.prog_id, "drift_rate", str(self.options.drift_rate.get()))
            self.conf_parser.set(self.program_type.prog_id, "num_cycles", str(self.options.num_cal_cycles.get()))
            self.conf_parser.set(self.program_type.prog_id, "target_temps", ",".join(str(x) for x in self.options.get_target_temps()))

        with open(os.path.join("cnfig", "prog_config.cfg"), "w") as pcfg:
            self.conf_parser.write(pcfg)

    def pause_program(self):
        """Pauses the program."""
        self.start_btn.configure(text=self.program_type.start_title)
        # self.header.configure(text=self.program_type.title)
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
        return await dev_helper.avg_waves_amps(self.master.laser, self.master.switch, self.switches,
                                         self.options.num_pts.get(), self.master.after)

    def on_closing(self):
        """Stops the user from closing if the program is running."""
        if self.running:
            if mbox.askyesno("Quit",
                             "Program is currently running. Are you sure you want to quit?"):
                self.master.destroy()
            else:
                self.master.tkraise()
        else:
            self.master.destroy()


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
        NavigationToolbar2TkAgg.__init__(self, self.figure_canvas, self.parent)

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
