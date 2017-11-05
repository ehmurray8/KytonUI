"""Module contains the main entry point for the Kyton UI."""

# pylint: disable=import-error, relative-import

import queue
import matplotlib
matplotlib.use("TkAgg")
import matplotlib.animation as animation
from matplotlib import style
from tkinter import messagebox
from tkinter import ttk
import tkinter as tk
import program
import ui_helper
import visa

style.use('ggplot')

LARGE_FONT = ("Verdana", 16)

OVEN = "Dicon Oven"
OVEN_LOC = 27

LASER = "Micron Optics SM125"
LASER_LOC = "10.0.0.122"
LASER_PORT = 50000

SWITCH = "Optical Switch"
SWITCH_LOC = "192.168.1.111"
SWITCH_PORT = 5000

TEMP = "LSC Temperature Controller"
TEMP_LOC = 12

CAL_NUM = -1

white = "#f0eff4"
az_white = "#dcedff"
lcbl_blue = "#94b0da"
onyx = "#343f3e"
nickel = "#727d71"

med_blue = "#0B3C5D"
sky_blue = "#328CC1"
gold = "#D9B310"
black = "#1D2731"

bg_color = black
tab_color = sky_blue
tabs_color = az_white
button_color = sky_blue
text_color = gold


class Application(tk.Tk):
    """Main Application class."""

    def __init__(self, *args, **kwargs):
        # pylint: disable=missing-super-argument
        super().__init__(*args, **kwargs)

        # Setup main window and styling
        self.title("Kyton FBG UI")
        img = tk.PhotoImage(file=r'fiber.png')
        self.tk.call('wm', 'iconphoto', self._w, img)

        style = ttk.Style()
        style.theme_create("outer", parent="alt", settings={
             ".": {"configure": {"background": bg_color}},
            "TFrame": {"configure": {"background": bg_color}},
            "TButton": {"configure": {"background": button_color, "font": ('Helvetica', 16), "foreground": text_color}},
            "TLabel": {"configure": {"font": ('Helvetica', 16), "foreground": text_color}},
            "TNotebook": {"configure": {"tabmargins": [10, 10, 10, 2]}},
            "TNotebook.Tab": {
                "configure": {"padding": [10, 4], "font": ('Helvetica', 18), "background": tab_color},
                "map":       {"background": [("selected", tabs_color)], "font": [("selected", ('Helvetica', 18, "bold"))],
                              "expand": [("selected", [1, 1, 1, 0])]}}})

        style.theme_use("outer")

        self.main_notebook = ttk.Notebook()
        self.main_notebook.enable_traversal()

        self.home_frame = ttk.Frame()
        self.main_notebook.add(self.home_frame, text="Home")
        self.main_notebook.pack(side="top", fill="both", expand=True)

        self.device_widgets = []
        self.main_queue = queue.Queue()
        
        # TODO setup args parse for testing purposes
        #self.manager = visa.ResourceManager()

        self.temp_controller = None
        self.oven = None
        self.laser = None
        self.switch = None

        self.cal_tab = None
        self.bake_tabs = []

        self.setup_home_frame()

        pad = 3
        self.geometry("{0}x{1}+0+0".format(
            self.winfo_screenwidth() - pad, self.winfo_screenheight() - pad))

    def setup_home_frame(self):
        device_frame = ttk.Frame(self.home_frame)

        ttk.Label(device_frame, text="Device").grid(sticky='ew')
        ttk.Label(device_frame, text="Location").grid(
            row=0, column=1, sticky='ew')
        ttk.Label(device_frame, text="Port").grid(row=0, column=2, sticky='ew')
        ttk.Button(device_frame, text="Connection Status").grid(
            row=0, column=3, sticky='ew')
        switch_conf = [(LASER, LASER_LOC, LASER_PORT), (SWITCH, SWITCH_LOC, SWITCH_PORT),
                       (TEMP, TEMP_LOC, None), (OVEN, OVEN_LOC, None)]
        for i, dev in enumerate(switch_conf):
            self.device_entry(device_frame, dev[0], dev[1], i + 1, dev[2])
        device_frame.grid(sticky='ew')

        start_prog_frame = ttk.Frame(self.home_frame)
        ttk.Button(start_prog_frame, text="Start New Baking Run",
                   command=self.create_bake_tab).pack()
        ttk.Button(start_prog_frame, text="Start New Calibration Run",
                   command=self.create_cal_tab).pack()
        start_prog_frame.grid(sticky='ew', row=0, column=1)

    def device_entry(self, container, dev_text, loc_str, row, port_str):
        """Creates an entry in the device grid for a device."""
        ttk.Entry(container, text=dev_text).grid(row=row, sticky='ew')

        loc_ent = ttk.Entry(container, text=loc_str)
        loc_ent.grid(row=row, column=1, sticky='ew')

        port_ent = None
        if port_str is not None:
            port_ent = ttk.Entry(container, text=port_str)
            port_ent.grid(row=row, sticky='ew', column=2)

        conn_butt = ttk.Button(container, text="Connect",
                command=lambda: self.conn_dev(loc_ent, port_ent, dev_text)
        conn_butt.grid(row=row, column=3, sticky='ew')

        self.device_widgets.append((loc_ent, port_ent, conn_butt))

    def conn_dev(self, loc_ent, port_ent, dev):
        if dev == TEMP:
            try:
                self.temp_controller = devices.TempController(
                    int(loc_ent.get()), self.manager)
            except visa.VisaIOError:
                # Need to handle Connection Error
                pass
            except ValueError:
                # Need to handle invalid value
                pass
        elif dev == OVEN:
            try:
                self.oven = devices.Oven("GPIB0::{}::INSTR".format(
                    int(loc_ent.get())), self.manager)
            except visa.VisaIOError:
                # Need to handle Connection Error
                pass
            except ValueError:
                # Need to handle invalid value
                pass
        elif dev == SWITCH:
            try:
                self.op_switch = devices.OpSwitch(
                    loc_ent.get(), int(port_ent.get()))
            except socket.error:
                # Need to handle connection error
                pass
            except:
                # Need to handle invalid value
                pass
        elif dev == LASER:
            try:
                self.laser = devices.SM125(loc_ent.get(), int(port_ent.get()))
            except socket.error:
                # Need to handle connection error
                pass
            except ValueError:
                # Need to handle invalid value
                pass

    def create_bake_tab(self):
        # Need to add logic for confirming, and deleting any cal tabs
        bake = program.Program(self, len(self.bake_tabs), program.BAKING_ID)
        self.bake_tabs.append(bake)
        self.main_notebook.add(
            bake, text="Bake {}".format(len(self.bake_tabs)))

    def create_cal_tab(self):
        # Need to add logic for confirming, and deleting any bake tabs
        if self.cal_tab is None:
            self.cal_tab = program.Program(self, CAL_NUM, program.CAL_ID)
            self.main_notebook.add(self.cal_tab, text="Calibration")
        else:
            # Need to handle warning user 1 Cal Max
            pass

    def delete_tab(self, id):
        if id == CAL_NUM:
            self.main_notebook.forget(self.cal_tab)
            self.cal_tab = None
        else:
            self.main_notebook.forget(self.bake_tabs[id])
            del self.bake_tabs[id]

    def tkloop(self):
        """Loop for threaded processes."""
        try:
            while True:
                func, args, kwargs = self.main_queue.get_nowait()
                func(*args, **kwargs)
        except queue.Empty:
            pass

        self.after(200, self.tkloop)


if __name__ == "__main__":
    APP = Application()
    APP.tkloop()
    APP.mainloop()
