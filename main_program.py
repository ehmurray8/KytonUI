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
import program
import devices
import visa
import argparse
from baking_program import BakingPage
from cal_program import CalPage
style.use('ggplot')


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

gray = "#B0ABA0"

#bg_color = onyx
bg_color = black
tab_color = sky_blue
tabs_color = az_white
#entry_color = az_white
#button_color = nickel
entry_color = gray
button_color = gray
#text_color = az_white
text_color = white


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

        style = ttk.Style()
        style.theme_create("outer", parent="alt", settings={
             ".": {"configure": {"background": bg_color}},
             "TFrame": {"configure": {"background": bg_color, "margin": [10, 10, 10, 10]}},
             "TButton": {"configure": {"background": button_color, "font": ('Helvetica', 16), "foreground": text_color, "justify": "center"}},
             "Bold.TLabel": {"configure": {"font": ('Helvetica', 18, 'bold')}},
            "TLabel": {"configure": {"font": ('Helvetica', 16), "foreground": text_color}},
            "TEntry": {"configure": {"font": ('Helvetica', 14), "background": entry_color}},
            "TNotebook": {"configure": {"tabmargins": [10, 10, 10, 2]}},
            "TCheckbutton": {"configre": {"height": 40, "width":40}},
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
        
        if self.use_dev:
            self.manager = visa.ResourceManager()

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
        col = 0
        device_frame.grid_columnconfigure(col, minsize=10)
        col = 2
        while col < 8:
            device_frame.grid_columnconfigure(col, minsize=20)
            col += 2
        device_frame.grid_columnconfigure(col, minsize=100)
        device_frame.grid_rowconfigure(0, minsize=10)
        ent_style = ttk.Style()

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
        ttk.Button(start_prog_frame, text="Start New Baking Run", compound=tk.CENTER, pad=5,
                   command=self.create_bake_tab).grid(sticky='ew')
        start_prog_frame.grid_rowconfigure(2, minsize=50)
        ttk.Button(start_prog_frame, text="Start New Calibration Run", compound=tk.CENTER, pad=5,
                   command=self.create_cal_tab).grid(row=3, sticky='ew')
        start_prog_frame.grid(sticky='ew', row=0, column=1)

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
                command=lambda: self.conn_dev(loc_ent, port_ent, dev_text))
        conn_butt.grid(row=row, column=7, sticky='ew')

        self.device_widgets.append((loc_ent, port_ent, conn_butt))

    

    def conn_dev(self, loc_ent, port_ent, dev):
        if self.use_dev:
            if dev == TEMP:
                try:
                    self.temp_controller = devices.TempController(
                        int(loc_ent.get()), self.manager)
                except visa.VisaIOError:
                    conn_warning(dev)
                except ValueError:
                    loc_warning("GPIB address")
            elif dev == OVEN:
                try:
                    self.oven = devices.Oven("GPIB0::{}::INSTR".format(
                        int(loc_ent.get())), self.manager)
                except visa.VisaIOError:
                    conn_warning(dev)
                except ValueError:
                    loc_warning("GPIB address")
            elif dev == SWITCH:
                try:
                    self.op_switch = devices.OpSwitch(
                        loc_ent.get(), int(port_ent.get()))
                except socket.error:
                    conn_warning(dev)
                except:
                    loc_warning("ethernet port")
            elif dev == LASER:
                try:
                    self.laser = devices.SM125(loc_ent.get(), int(port_ent.get()))
                except socket.error:
                    conn_warning(dev)
                except ValueError:
                    loc_warning("ethernet port")

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

def conn_warning(dev):
    messagebox.showwarning("Connection Error", "Currently unable to connect to {},".format(dev) +
            "make sure the device is connected to the computer and the location information is correct.")

def loc_warning(type):
    messagebox.showwarning("Invalid Location", "Please import an integer corresponding to the {}.".format(type))


if __name__ == "__main__":
    APP = Application()
    APP.tkloop()
    APP.mainloop()
