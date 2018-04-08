"""Module contains the main entry point for the Kyton UI."""

import argparse
import configparser
import os
import sys
import platform
import socket
from queue import Queue, Empty
from tkinter import ttk
from shutil import copy2

import matplotlib
import visa
from fbgui.baking_program import BakingProgram
from fbgui.cal_program import CalProgram
from fbgui import create_excel, constants, devices

matplotlib.use("TkAgg")
from tkinter import messagebox as mbox
import tkinter as tk
if platform.system() == "Linux":
    from ttkthemes import ThemedStyle


class Message(object):

    def __init__(self, warning, is_warn, args):
        self.warning_type = warning
        self.is_warning = is_warn
        self.args = args


class WarningHandler(object):

    def __init__(self):
        self.warnings = {"Excel": False, "File": False, "Program Running": False, "Config": False, "Location": False,
                         "Connection": False}
        pass

    def handle_msg(self, msg):
        """
        Handles showing a messagebox to the user without repeating itself.

        :param msg: Message object
        :return: A tuple of the title, and message for the message box.
        """
        if not self.warnings[msg.warning_type] and msg.is_warning:
            if msg.warning_type == "Excel":
                return ("Excel File Generation Error",
                        "No data has been recorded yet, or the database has been corrupted.")
            elif msg.warning_type == "File":
                return "File Error",

        elif not msg.is_warning:
            self.warnings[msg.warning_type] = False


class Application(tk.Tk):
    """Main Application class."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        site_packs = [s for s in sys.path if 'site-packages' in s][0]
        copy2(os.path.join("assets", "kyton.mplstyle"), os.path.join(site_packs, "matplotlib", "mpl-data", "stylelib"))
        copy2(os.path.join("assets", "play.gif"), os.path.join(site_packs, "matplotlib", "mpl-data", "images"))
        copy2(os.path.join("assets", "pause.gif"), os.path.join(site_packs, "matplotlib", "mpl-data", "images"))

        self.use_dev = arg_parse()

        self.conf_parser = configparser.ConfigParser()
        self.conf_parser.read(os.path.join("config", "devices.cfg"))

        self.style = ttk.Style()
        fiber_path = os.path.join("assets", "fiber.png")
        self.is_fullscreen = self.setup_window(fiber_path)

        self.main_notebook = ttk.Notebook(self)
        self.main_notebook.enable_traversal()

        self.home_frame = ttk.Frame(self.main_notebook)
        self.main_notebook.add(self.home_frame, text="Home")
        self.main_notebook.pack(side="top", fill="both", expand=True)
        self.running_prog = None

        self.device_widgets = []
        if self.use_dev:
            self.manager = visa.ResourceManager()
        else:
            self.manager = None

        self.bake = None
        self.cal = None
        self.running = False

        self.temp_controller = None
        self.oven = None
        self.laser = None
        self.switch = None

        self.controller_location = tk.IntVar()
        self.oven_location = tk.IntVar()
        self.op_switch_address = tk.StringVar()
        self.op_switch_port = tk.IntVar()
        self.sm125_address = tk.StringVar()
        self.sm125_port = tk.IntVar()

        self.setup_home_frame()

        # Create the program tabs
        self.create_bake_tab()
        self.create_cal_tab()

        self.main_queue = Queue()

    def check_queue(self):
        while True:
            msg = ""
            try:
                msg = self.main_queue.get(timeout=0.1)
            except Empty:
                break
            # Handle message

        self.after(10000, self.check_queue)

    def toggle_fullscreen(self, _=None):
        """Toggles full screen on and off."""
        self.is_fullscreen = not self.is_fullscreen
        self.attributes("-fullscreen", self.is_fullscreen)
        return "break"

    def end_fullscreen(self, _=None):
        """Exit full screen"""
        self.is_fullscreen = False
        self.attributes("-fullscreen", False)
        return "break"

    def setup_home_frame(self):
        """Sets up the home frame as TK frame that is displayed on launch."""
        hframe = ttk.Frame(self.home_frame)
        hframe.pack()
        device_frame = ttk.Frame(hframe)
        col = 0
        device_frame.grid_columnconfigure(col, minsize=10)
        col = 2
        while col < 8:
            device_frame.grid_columnconfigure(col, minsize=20)
            col += 2
        device_frame.grid_columnconfigure(col, minsize=100)
        device_frame.grid_rowconfigure(0, minsize=10)

        ttk.Label(device_frame, text="Device", style="Bold.TLabel").grid(row=1, column=1, sticky='nsew')
        ttk.Label(device_frame, text="Location", style="Bold.TLabel").grid(row=1, column=3, sticky='nsew')
        ttk.Label(device_frame, text="Port", style="Bold.TLabel").grid(row=1, column=5, sticky='nsew')
        laser_loc = self.conf_parser.get(constants.DEV_HEADER, "sm125_address")
        laser_port = self.conf_parser.get(constants.DEV_HEADER, "sm125_port")
        switch_loc = self.conf_parser.get(constants.DEV_HEADER, "op_switch_address")
        switch_port = self.conf_parser.get(constants.DEV_HEADER, "op_switch_port")
        temp_loc = self.conf_parser.get(constants.DEV_HEADER, "controller_location")
        oven_loc = self.conf_parser.get(constants.DEV_HEADER, "oven_location")
        switch_conf = [(constants.LASER, laser_loc, laser_port, self.sm125_address, self.sm125_port),
                       (constants.SWITCH, switch_loc, switch_port, self.op_switch_address, self.op_switch_port),
                       (constants.TEMP, temp_loc, None, self.controller_location, None),
                       (constants.OVEN, oven_loc, None, self.oven_location, None)]
        for i, dev in enumerate(switch_conf):
            device_frame.grid_rowconfigure(i * 2, pad=20)
            self.device_entry(device_frame, dev[0], dev[1], i + 2, dev[2], dev[3], dev[4])
        device_frame.pack(anchor=tk.CENTER, expand=True, pady=15)
        create_excel.Table(hframe).pack(pady=175, anchor=tk.S, expand=True)

    def device_entry(self, container, dev_text, loc_str, row, port_str, loc_var, port_var):
        """Creates an entry in the device grid for a device."""
        dev_widg = ttk.Label(container, text=dev_text)
        dev_widg.grid(row=row, column=1, sticky='nsew')

        loc_ent = ttk.Entry(container, font="Helvetica 14", textvariable=loc_var)
        loc_ent.delete(0, tk.END)
        loc_ent.insert(tk.INSERT, loc_str)
        loc_ent.grid(row=row, column=3, sticky='ew')

        if port_str is not None:
            port_ent = ttk.Entry(container, font="Helvetica 14", textvariable=port_var)
            port_ent.delete(0, tk.END)
            port_ent.insert(tk.INSERT, port_str)
            port_ent.grid(row=row, sticky='ew', column=5)

    def conn_dev(self, dev: str, connect: bool=True, try_once: bool=False):
        """
        Connects or Disconnects the program to a required device based on the input location params.
        """
        err_specifier = "Unknown error"
        need_conn_warn = False
        need_loc_warn = False

        num = 3
        if try_once:
            num = 1

        # TODO: Fix this to properly warn and try forever
        for _ in range(num):
            try:
                if dev == constants.TEMP:
                    if connect:
                        if self.temp_controller is None:
                            err_specifier = "GPIB address"
                            temp_loc = self.conf_parser.get(constants.DEV_HEADER, "controller_location")
                            self.temp_controller = devices.TempController(int(temp_loc), self.manager, self.use_dev)
                    else:
                        self.temp_controller.close()
                        self.temp_controller = None
                elif dev == constants.OVEN:
                    if connect:
                        if self.oven is None:
                            err_specifier = "GPIB address"
                            oven_loc = self.conf_parser.get(constants.DEV_HEADER, "oven_location")
                            self.oven = devices.Oven(int(oven_loc), self.manager, self.use_dev)
                    else:
                        self.oven.close()
                        self.oven = None
                elif dev == constants.SWITCH:
                    if connect:
                        if self.switch is None:
                            err_specifier = "ethernet port"
                            switch_loc = self.conf_parser.get(constants.DEV_HEADER, "op_switch_address")
                            switch_port = self.conf_parser.get(constants.DEV_HEADER, "op_switch_port")
                            self.switch = devices.OpSwitch(switch_loc, int(switch_port), self.use_dev)
                    else:
                        self.switch.close()
                        self.switch = None
                elif dev == constants.LASER:
                    if connect:
                        if self.laser is None:
                            err_specifier = "ethernet port"
                            laser_loc = self.conf_parser.get(constants.DEV_HEADER, "sm125_address")
                            laser_port = self.conf_parser.get(constants.DEV_HEADER, "sm125_port")
                            self.laser = devices.SM125(laser_loc, int(laser_port), self.use_dev)
                    else:
                        self.laser.close()
                        self.laser = None

                need_conn_warn = False
                need_loc_warn = False
                break
            except socket.error:
                need_conn_warn = True
            except visa.VisaIOError:
                need_conn_warn = True
            except ValueError:
                need_loc_warn = True

        if need_conn_warn:
            if try_once:
                conn_warning(dev)
        elif need_loc_warn:
            if try_once:
                loc_warning(err_specifier)

    def create_bake_tab(self):
        """Create a tab used for a baking run."""
        self.bake = BakingProgram(self)
        self.main_notebook.add(self.bake, text="Bake")

    def create_cal_tab(self):
        """Create a tab used for a calibration run."""
        self.cal = CalProgram(self)
        self.main_notebook.add(self.cal, text="Calibration")

    def on_closing(self):
        if self.running:
            if mbox.askyesno("Quit",
                             "Program is currently running. Are you sure you want to quit?"):
                if self.oven is not None:
                    self.oven.close()
                if self.temp_controller is not None:
                    self.temp_controller.close()
                if self.switch is not None:
                    self.switch.close()
                if self.laser is not None:
                    self.laser.close()
                self.destroy()
            else:
                self.tkraise()
        else:
            self.destroy()

    def setup_window(self, fiber_path):
        self.title("Kyton FBG UI")
        img = tk.PhotoImage(file=fiber_path)
        self.tk.call('wm', 'iconphoto', self._w, img)

        self.state("zoomed")

        parent_theme = "winnative"
        if platform.system() == "Linux":
            self.style = ThemedStyle(self)
            parent_theme = "clearlooks"
        self.style.theme_create("main", parent=parent_theme, settings={
            ".": {"configure": {"background": constants.BG_COLOR}},
            "TFrame": {"configure": {"background": constants.BG_COLOR, "margin": [10, 10, 10, 10]}},
            "TButton": {"configure": {"background": constants.BUTTON_COLOR, "font": ('Helvetica', 16),
                                      "foreground": constants.BUTTON_TEXT, "justify": "center"}},
            "Bold.TLabel": {"configure": {"font": ('Helvetica', 18, 'bold')}},
            "TLabel": {"configure": {"font": ('Helvetica', 16), "foreground": constants.TEXT_COLOR}},
            "TEntry": {"configure": {"font": ('Helvetica', 14)},
                       "map":       {"fieldbackground": [("active", constants.ENTRY_COLOR),
                                                         ("disabled", constants.BG_COLOR)],
                                     "foreground": [("active", "black"),
                                                    ("disabled", constants.TEXT_COLOR)]}},
            "Treeview": {"configure":
                         {"foreground": constants.Colors.WHITE, "background": constants.BG_COLOR},
                         "map": {"background": [("selected", constants.TABS_COLOR)],
                                 "font": [("selected", ('Helvetica', 10, "bold"))],
                                 "foreground": [("selected", constants.Colors.BLACK)]}
                         },
            "Treeview.Heading": {"configure": {"foreground": constants.TEXT_COLOR,
                                               "font": {("Helvetica", 12, "bold")}, "sticky": "ew"}},
            "TNotebook": {"configure": {"tabmargins": [10, 10, 10, 2]}},
            "TCheckbutton": {"configre": {"height": 40, "width": 40}},
            "TNotebook.Tab": {
                "configure": {"padding": [10, 4], "font": ('Helvetica', 18),
                              "background": constants.TAB_COLOR},
                "map":       {"background": [("selected", constants.TABS_COLOR)],
                              "font": [("selected", ('Helvetica', 18, "bold"))],
                              "expand": [("selected", [1, 1, 1, 0])]}}})

        # Used exclusively for development purposes
        if platform.system() == "Linux":
            self.style.set_theme("main")
        else:
            self.style.theme_use("main")
        self.protocol("WM_DELETE_WINDOW", self.on_closing)
        self.geometry("{0}x{1}+0+0".format(self.winfo_screenwidth(), self.winfo_screenheight()))
        # Sets up full screen key bindings
        self.bind("<F11>", self.toggle_fullscreen)
        self.bind("<Escape>", self.end_fullscreen)
        return False


def arg_parse():
    parser = argparse.ArgumentParser(description='Run the Kyton program for the correct computer.')
    parser.add_argument('--nodev', action="store_true", help='Use this arg if no devices are available.')
    use_dev = True
    cmdargs = parser.parse_args()
    if cmdargs.nodev:
        use_dev = False
    return use_dev


def conn_warning(dev):
    """Warn the user that there was an error connecting to a device."""
    mbox.showwarning("Connection Error", "Currently unable to connect to {},".format(dev) +
                     "make sure the device is connected to the computer and the location " +
                     "information is correct.")


def loc_warning(loc_type):
    """Warn the user of an invalid location input."""
    mbox.showwarning(
        "Invalid Location", "Please import an integer corresponding to the {}.".format(loc_type))


if __name__ == "__main__":
    APP = Application()
    APP.mainloop()
