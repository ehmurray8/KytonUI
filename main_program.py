"""Module contains the main entry point for the Kyton UI."""

# pylint: disable=import-error, relative-import

import queue
import socket
import matplotlib

matplotlib.use("TkAgg")
from matplotlib import style
from tkinter import messagebox
from tkinter import ttk
import tkinter as tk
import platform
if platform.system() == "Linux":
    from ttkthemes import ThemedStyle
import devices
import visa
import argparse
from baking_program import BakingPage
from cal_program import CalPage
import colors
style.use('kyton')


OVEN = "Delta Oven"
OVEN_LOC = 27

LASER = "Micron Optics SM125"
LASER_LOC = "192.168.1.203"
LASER_PORT = 50000

SWITCH = "Optical Switch"
SWITCH_LOC = "192.168.1.111"
SWITCH_PORT = 5000

TEMP = "LSC Temperature Controller"
TEMP_LOC = 12

CAL_NUM = -1


class Application(tk.Tk):
    """Main Application class."""

    def __init__(self, *args, **kwargs):
        # pylint: disable=missing-super-argument
        super().__init__(*args, **kwargs)

        parser = argparse.ArgumentParser(description='Run the Kyton program for the correct computer.')
        parser.add_argument('--nodev', action="store_true", help='Use this arg if no devices are available.')
        self.use_dev = True
        cmdargs = parser.parse_args()
        if cmdargs.nodev:
            self.use_dev = False

        # Setup main window and styling
        self.title("Kyton FBG UI")
        img = tk.PhotoImage(file=r'fiber.png')
        self.tk.call('wm', 'iconphoto', self._w, img)

        self.style = ttk.Style()
        parent_theme = "winnative"
        if platform.system() == "Linux":
            self.style = ThemedStyle(self)
            parent_theme = "clearlooks"
        self.style.theme_create("main", parent=parent_theme, settings={
             ".": {"configure": {"background": colors.BG_COLOR}},
             "TFrame": {"configure": {"background": colors.BG_COLOR, "margin": [10, 10, 10, 10]}},
             "TButton": {"configure": {"background": colors.BUTTON_COLOR, "font": ('Helvetica', 16),
                                       "foreground": colors.BUTTON_TEXT, "justify": "center"}},
             "Bold.TLabel": {"configure": {"font": ('Helvetica', 18, 'bold')}},
            "TLabel": {"configure": {"font": ('Helvetica', 16), "foreground": colors.TEXT_COLOR}},
            "TEntry": {"configure": {"font": ('Helvetica', 14), "background": colors.ENTRY_COLOR}},
            "TNotebook": {"configure": {"tabmargins": [10, 10, 10, 2]}},
            "TCheckbutton": {"configre": {"height": 40, "width":40}},
            "TNotebook.Tab": {
                "configure": {"padding": [10, 4], "font": ('Helvetica', 18), "background": colors.TAB_COLOR},
                "map":       {"background": [("selected", colors.TABS_COLOR)], "font": [("selected", ('Helvetica', 18, "bold"))],
                              "expand": [("selected", [1, 1, 1, 0])]}}})

        if platform.system() == "Linux":
            self.style.set_theme("main")
        else:
            self.style.theme_use("main")

        self.main_notebook = ttk.Notebook()
        self.main_notebook.enable_traversal()

        self.home_frame = ttk.Frame()
        self.main_notebook.add(self.home_frame, text="Home")
        self.main_notebook.pack(side="top", fill="both", expand=True)

        self.device_widgets = []
        self.main_queue = queue.Queue()
        
        if self.use_dev:
            self.manager = visa.ResourceManager()

        self.temp_controller = None
        self.oven = None
        self.laser = None
        self.switch = None

        self.cal_tab = None
        self.bake_tabs = []

        self.setup_home_frame()

        self.geometry("{0}x{1}+0+0".format(
            self.winfo_screenwidth(), self.winfo_screenheight()))
        self.attributes("-fullscreen", True)
        self.state = True
        self.bind("<F11>", self.toggle_fullscreen)
        self.bind("<Escape>", self.end_fullscreen)

    def toggle_fullscreen(self, event=None):
        self.state = not self.state  # Just toggling the boolean
        self.attributes("-fullscreen", self.state)
        return "break"

    def end_fullscreen(self, event=None):
        self.state = False
        self.attributes("-fullscreen", False)
        return "break"

    def setup_home_frame(self):
        device_frame = ttk.Frame(self.home_frame)
        col = 0
        device_frame.grid_columnconfigure(col, minsize=10)
        col = 2
        while col < 8:
            device_frame.grid_columnconfigure(col, minsize=20)
            col += 2
        device_frame.grid_columnconfigure(col, minsize=100)
        device_frame.grid_rowconfigure(0, minsize=10)

        ttk.Label(device_frame, text="Device", style="Bold.TLabel").grid(row=1, column=1, sticky='ew')
        ttk.Label(device_frame, text="Location", style="Bold.TLabel").grid(
            row=1, column=3, sticky='ew')
        ttk.Label(device_frame, text="Port", style="Bold.TLabel").grid(row=1, column=5, sticky='ew')
        ttk.Label(device_frame, text="Connection Status", style="Bold.TLabel").grid(
            row=1, column=7, sticky='ew')
        switch_conf = [(LASER, LASER_LOC, LASER_PORT), (SWITCH, SWITCH_LOC, SWITCH_PORT),
                       (TEMP, TEMP_LOC, None), (OVEN, OVEN_LOC, None)]
        for i, dev in enumerate(switch_conf):
            device_frame.grid_rowconfigure(i*2, pad=20)
            self.device_entry(device_frame, dev[0], dev[1], i+2, dev[2])
        device_frame.grid(sticky='ew')

        start_prog_frame = ttk.Frame(self.home_frame)
        start_prog_frame.grid_columnconfigure(0, minsize=300)
        start_prog_frame.grid_columnconfigure(2, minsize=70)
        ttk.Button(start_prog_frame, text="Start New Baking Run", compound=tk.CENTER, pad=5,
                   command=self.create_bake_tab).grid(row=1, column=1, sticky='ew')
        ttk.Button(start_prog_frame, text="Start New Calibration Run", compound=tk.CENTER, pad=5,
                   command=self.create_cal_tab).grid(row=1, column=3, sticky='ew')
        start_prog_frame.grid(sticky='ew', row=2, column=0)
        self.home_frame.grid_rowconfigure(1, minsize=50)

    def device_entry(self, container, dev_text, loc_str, row, port_str):
        """Creates an entry in the device grid for a device."""
        dev_widg = ttk.Label(container, text=dev_text)
        dev_widg.grid(row=row, column=1, sticky='ew')

        loc_ent = ttk.Entry(container, font="Helvetica 14")
        loc_ent.insert(tk.INSERT, loc_str)
        loc_ent.grid(row=row, column=3, sticky='ew')

        port_ent = None
        if port_str is not None:
            port_ent = ttk.Entry(container, font="Helvetica 14")
            port_ent.insert(tk.INSERT, port_str)
            port_ent.grid(row=row, sticky='ew', column=5)

        conn_butt = ttk.Button(container, text="Connect",
                command=lambda: self.conn_dev(loc_ent, port_ent, dev_text, conn_butt))
        conn_butt.grid(row=row, column=7, sticky='ew')

        self.device_widgets.append((loc_ent, port_ent, conn_butt))

    def conn_dev(self, loc_ent, port_ent, dev, button):
        connect = False
        if self.use_dev:
            if dev == TEMP:
                if self.temp_controller is None:
                    try:
                        self.temp_controller = devices.TempController(
                            int(loc_ent.get()), self.manager)
                        connect = True
                    except visa.VisaIOError:
                        conn_warning(dev)
                    except ValueError:
                        loc_warning("GPIB address")
                else:
                    self.temp_controller.close()
                    self.temp_controller = None
            elif dev == OVEN:
                if self.oven is None:
                    try:
                        self.oven = devices.Oven(int(loc_ent.get()), self.manager)
                        connect = True
                    except visa.VisaIOError:
                        conn_warning(dev)
                    except ValueError:
                        loc_warning("GPIB address")
                else:
                    self.oven.close()
                    self.oven = None
            elif dev == SWITCH:
                if self.switch is None:
                    try:
                        self.switch = devices.OpSwitch(
                            loc_ent.get(), int(port_ent.get()))
                        connect = True
                    except socket.error:
                        conn_warning(dev)
                    except ValueError:
                        loc_warning("ethernet port")
                else:
                    self.switch.close()
                    self.switch = None
            elif dev == LASER:
                if self.laser is None:
                    try:
                        self.laser = devices.SM125(loc_ent.get(), int(port_ent.get()))
                        connect = True
                    except socket.error:
                        conn_warning(dev)
                    except ValueError:
                        loc_warning("ethernet port")
                else:
                    self.laser.close()
                    self.laser = None
        if connect:
            button['text'] = "Disconnect"
        else:
            button['text'] = "Connect"


    def create_bake_tab(self):
        # Need to add logic for confirming, and deleting any cal tabs
        if self.cal_tab is None:
            bake = BakingPage(self, len(self.bake_tabs))
            self.bake_tabs.append(bake)
            self.main_notebook.add(
                bake, text="Bake {}".format(len(self.bake_tabs)))
        else:
            messagebox.showwarning("Calibration Program Open", 
                    "A calibration program is already open, only one cal can be run at the same time.")

    def create_cal_tab(self):
        # Need to add logic for confirming, and deleting any bake tabs
        if self.cal_tab is None and not len(self.bake_tabs):
            self.cal_tab = CalPage(self, CAL_NUM)
            self.main_notebook.add(self.cal_tab, text="Calibration")
        elif len(self.bake_tabs):
            messagebox.showwarning("Bake Programs Open", 
                    "Cannot open a calibration program while Bake programs are open, please close all bake tabs before continuing.")
        else:
            messagebox.showwarning("Calibration Program Open", 
                    "A calibration program is already open, only one cal can be run at the same time.")

    def delete_tab(self, prog_id):
        if prog_id == CAL_NUM:
            self.main_notebook.forget(self.cal_tab)
            self.cal_tab = None
        else:
            self.main_notebook.forget(self.bake_tabs[prog_id])
            del self.bake_tabs[prog_id]

    def tkloop(self):
        """Loop for threaded processes."""
        try:
            while True:
                func, args, kwargs = self.main_queue.get_nowait()
                func(*args, **kwargs)
        except queue.Empty:
            pass

        self.after(200, self.tkloop)


def conn_warning(dev):
    messagebox.showwarning("Connection Error", "Currently unable to connect to {},".format(dev) +
                           "make sure the device is connected to the computer and the location information is correct.")


def loc_warning(loc_type):
    messagebox.showwarning("Invalid Location", "Please import an integer corresponding to the {}.".format(loc_type))


if __name__ == "__main__":
    APP = Application()
    APP.tkloop()
    APP.mainloop()
