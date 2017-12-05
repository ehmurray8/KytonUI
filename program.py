"""
Abstract class defines common functionality between calibration
program and baking program.
"""

# pylint: disable=import-error, relative-import, protected-access, superfluous-parens
import time
from tkinter import ttk, messagebox as mbox
import platform
from PIL import Image, ImageTk
import tkinter as tk
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2TkAgg
from matplotlib.figure import Figure
import options_frame
import file_helper as fh
import graphing
import ui_helper

BAKING_ID = "Baking"
CAL_ID = "Cal"


class ProgramType(object):  # pylint:disable=too-few-public-methods
    """Defines constants for each type of program."""

    def __init__(self, prog_id):
        self.prog_id = prog_id
        if self.prog_id == BAKING_ID:
            self.title = "Configure Baking"
            self.config_id = fh.BAKING_SECTION
            self.options = options_frame.BAKING
            self.in_prog_msg = "Baking..."
            self.plot_num = 230
            self.num_graphs = 6
        else:
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
        self.options = None
        self.start_btn = None
        self.data_pts = {}
        self.delayed_prog = None

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

    def start(self, can_start=False):
        """Starts the recording process."""
        switch_chan = -1
        chan = -2
        if not can_start:
            if self.delayed_prog is not None:
                    self.master.after_cancel(self.delayed_prog)
                    self.delayed_prog = None
            elif self.master.running:
                prog = "Baking"
                run = "calibration"
                if self.program_type.prog_id == BAKING_ID:
                    prog = "Calibration"
                    run = "bake"
                mbox.showwarning("{} program is already running".format(prog),
                                 "Please stop the {} program before starting the {}."
                                 .format(prog, run))
            elif not len(self.options.sn_ents):
                mbox.showwarning("Invalid configuration",
                                    "Please add fbg entries to your configuration before " +
                                    "running the program.")
            else:
                for chan, snum, pos in zip(self.options.chan_nums,
                                           self.options.sn_ents,
                                           self.options.switch_positions):
                    if snum.get() != "" and snum.get() not in self.snums:
                        self.snums.append(snum.get())
                        self.channels[chan].append(snum.get())
                        if pos.get() != 0:
                            if switch_chan != -1 and switch_chan != chan:
                                break
                            self.switches[chan].append(pos.get())
                            switch_chan = chan

                if switch_chan != -1 and switch_chan != chan:
                    mbox.showwarning("Invalid configuration",
                                     "Cannot have multiple channels configured to use the optical" +
                                     " switch.")
                    self.pause_program()
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
                    if self.program_type.prog_id == CAL_ID and self.master.oven is None:
                        need_oven = True
                        self.master.conn_buttons[3].invoke()

                    if self.master.laser is not None and (self.master.switch is not None or not need_switch) and \
                        self.master.temp_controller is not None and (self.master.oven is not None or not need_oven):

                        self.master.running = True
                        self.start_btn.configure(text="Pause")
                        # self.header.configure(text=self.program_type.in_prog_msg)
                        ui_helper.lock_widgets(self.options)
                        time.sleep(.1)
                        self.graph_helper.show_subplots()
                        time.sleep(.1)
                        self.delayed_prog = self.master.after(int(self.options.delay.get() *
                                                                1000 * 60 * 60 + .5),
                                                            self.program_loop)
                    else:
                        self.pause_program()
        else:
            self.program_loop()

    def pause_program(self):
        """Pauses the program."""
        self.start_btn.configure(text=self.program_type.title)
        # self.header.configure(text=self.program_type.title)
        ui_helper.unlock_widgets(self.options)
        self.running = False
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
