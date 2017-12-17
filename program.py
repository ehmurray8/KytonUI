"""
Abstract class defines common functionality between calibration
program and baking program.
"""

# pylint: disable=import-error, relative-import, protected-access, superfluous-parens
import os
from tkinter import ttk, messagebox as mbox
import platform
import configparser
from PIL import Image, ImageTk
import tkinter as tk
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2TkAgg
from matplotlib.figure import Figure
import options_frame
import file_helper as fh
import graphing
import ui_helper
import helpers as help

BAKING_ID = "Baking"
CAL_ID = "Cal"
BAKE_HEAD = "Baking"
CAL_HEAD = "Calibration"


class ProgramType(object):  # pylint:disable=too-few-public-methods
    """Defines constants for each type of program."""

    def __init__(self, prog_id):
        self.prog_id = prog_id
        if self.prog_id == BAKING_ID:
            self.start_title = "Start Baking"
            self.title = "Configure Baking"
            self.config_id = fh.BAKING_SECTION
            self.options = options_frame.BAKING
            self.in_prog_msg = "Baking..."
            self.plot_num = 230
            self.num_graphs = 6
        else:
            self.start_title = "Start Calibration"
            self.title = "Configure Calibration"
            self.config_id = fh.CAL_SECTION
            self.options = options_frame.CAL
            self.in_prog_msg = "Calibrating..."
            self.plot_num = 240
            self.num_graphs = 7


class Page(ttk.Notebook):  # pylint: disable=too-many-instance-attributes
    """Definition of the abstract program page."""

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
        self.data_pts = {}
        self.delayed_prog = None

        self.conf_parser = configparser.ConfigParser()
        self.conf_parser.read("prog_config.cfg")

        self.config_frame = ttk.Frame()
        self.graph_frame = ttk.Frame()

        # Need images as instance variables to prevent garbage collection
        config_path = r'assets\config.png'
        graph_path = r'assets\graph.png'
        if platform.system() == "Linux":
            config_path = "assets/config.png"
            graph_path = "assets/graph.png"
        img_config = Image.open(config_path)
        img_graph = Image.open(graph_path)

        self.img_config = ImageTk.PhotoImage(img_config)
        self.img_graph = ImageTk.PhotoImage(img_graph)

        # Set up config tab
        self.add(self.config_frame, image=self.img_config)
        self.options = options_frame.OptionsPanel(
            self.config_frame, self.program_type.options)
        self.start_btn = self.options.create_start_btn(self.start)
        self.xcel_btn = self.options.create_xcel_btn(self.create_excel)
        self.options.init_fbgs()
        self.options.grid_rowconfigure(1, minsize=20)
        self.options.grid_rowconfigure(3, minsize=20)
        self.options.grid_rowconfigure(5, minsize=20)
        self.options.pack(expand=True, side="right", fill="both")

        # Set up graphing tab
        self.add(self.graph_frame, image=self.img_graph)

        # Graphs need to be empty until csv is created
        self.fig = Figure(figsize=(5, 5), dpi=100)

        self.canvas = FigureCanvasTkAgg(self.fig, self.graph_frame)
        self.canvas.show()
        is_cal = False
        if self.program_type.prog_id == CAL_ID:
            is_cal = True

        self.canvas.get_tk_widget().pack(side=tk.BOTTOM, fill=tk.BOTH, expand=True)

        self.toolbar = Toolbar(self.canvas, self.graph_frame)
        self.toolbar.update()
        file_name = self.options.file_name
        self.graph_helper = graphing.Graphing(file_name, self.program_type.plot_num,
                                              is_cal, self.fig, self.canvas, self.toolbar,
                                              self.master)
        self.toolbar.set_gh(self.graph_helper)
        self.canvas._tkcanvas.pack(side=tk.TOP, fill=tk.BOTH, expand=True)

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

        if not fh.check_metadata(file_lines, num_conf_fbgs):
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
                if self.program_type.prog_id != BAKING_ID:
                    file_error(csv_file, "was created to be used for baking.")
                    valid_file = False
                else:
                    valid_file = self.valid_header(csv_file, file_lines) and valid_file
            elif "Caldata" in prog_header:
                if self.program_type.prog_id == BAKING_ID:
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
                    if self.program_type.prog_id == BAKING_ID:
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
                        if (self.program_type.prog_id == CAL_ID or self.options.set_temp.get()) \
                                and self.master.oven is None:
                            need_oven = True
                            self.master.conn_buttons[3].invoke()

                        if self.master.laser is not None and (self.master.switch is not None or not need_switch) and \
                                self.master.temp_controller is not None and (self.master.oven is not None or not need_oven):
                            self.save_config_info()
                            if need_oven:
                                self.master.oven.set_temp(self.options.set_temp.get())
                                self.master.oven.heater_on()
                            self.master.running = True
                            self.master.running_prog = self.program_type.prog_id
                            # self.header.configure(text=self.program_type.in_prog_msg)
                            ui_helper.lock_widgets(self.options)
                            self.graph_helper.show_subplots()
                            self.delayed_prog = self.master.after(int(self.options.delay.get() *
                                                                      1000 * 60 * 60 + .5),
                                                                  self.program_loop)
                        else:
                            self.pause_program()
                else:
                    self.pause_program()

    def save_config_info(self):
        self.conf_parser.set(BAKE_HEAD, "running", "true")
        self.conf_parser.set(CAL_HEAD, "running", "false")
        if self.program_type.prog_id == BAKING_ID:
            self.conf_parser.set(BAKE_HEAD, "num_scans", str(self.options.num_pts.get()))
            self.conf_parser.set(BAKE_HEAD, "set_temp", str(self.options.set_temp.get()))
            self.conf_parser.set(BAKE_HEAD, "init_delay", str(self.options.delay.get()))
            self.conf_parser.set(BAKE_HEAD, "init_interval", str(self.options.init_time.get()))
            self.conf_parser.set(BAKE_HEAD, "init_duration", str(self.options.init_duration.get()))
            self.conf_parser.set(BAKE_HEAD, "prim_interval", str(self.options.prim_time.get()))
            self.conf_parser.set(BAKE_HEAD, "file", str(self.options.file_name.get()))
            last_folder = os.path.dirname(self.options.file_name.get())
            self.conf_parser.set(BAKE_HEAD, "last_folder", last_folder)
            for i, (snums) in enumerate(self.channels):
                self.conf_parser.set(BAKE_HEAD, "chan{}_fbgs".format(i), ",".join(snums))
                if snums[0] in self.switches:
                    self.conf_parser.set(BAKE_HEAD, "chan{}_positions".format(i), ",".join(help.flatten(self.switches)))
                else:
                    self.conf_parser.set(BAKE_HEAD, "chan{}_positions".format(i), "")
            with open("prog_config.cfg", "w") as pcfg:
                self.conf_parser.write(pcfg)

    def pause_program(self):
        """Pauses the program."""
        self.start_btn.configure(text=self.program_type.start_title)
        # self.header.configure(text=self.program_type.title)
        ui_helper.unlock_widgets(self.options)
        self.master.running = False
        self.master.running_prog = None
        self.conf_parser.set(BAKE_HEAD, "running", "false")
        self.conf_parser.set(CAL_HEAD, "running", "false")
        self.stable_count = 0
        self.snums = []
        self.channels = [[], [], [], []]
        self.switches = [[], [], [], []]

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
