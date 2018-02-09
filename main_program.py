"""Module contains the main entry point for the Kyton UI."""

# pylint: disable=too-many-arguments, too-many-branches
# pylint: disable=too-many-instance-attributes
import os
from shutil import copy2
import socket
import argparse
from tkinter import ttk
import platform
import matplotlib
import configparser
import getpass
import visa

matplotlib.use("TkAgg")
import asyncio
from matplotlib import style
from tkinter import messagebox
import tkinter as tk
if platform.system() == "Linux":
    from ttkthemes import ThemedStyle
import devices
from baking_program import BakingProgram
from cal_program import CalProgram
import constants


class Application(tk.Tk):
    """Main Application class."""

    def __init__(self, *args, **kwargs):
        # pylint: disable=missing-super-argument
        super().__init__(*args, **kwargs)
        self.use_dev = arg_parse()

        self.conf_parser = configparser.ConfigParser()
        self.conf_parser.read(os.path.join("config", "devices.cfg"))

        self.style = ttk.Style()
        fiber_path = os.path.join("assets", "fiber.png")
        self.state = self.setup_window(fiber_path)

        self.main_notebook = ttk.Notebook()
        self.main_notebook.enable_traversal()

        self.home_frame = ttk.Frame()
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

        self.loop = asyncio.get_event_loop()
        self.conn_buttons = {}
        self.setup_home_frame()

        user = getpass.getuser()
        if platform.system() == "win32":
            copy2(os.path.join("install", "BakingCal.lnk"),
                  r"C:\Users\{}\AppData\Roaming\Microsoft\Windows\Start Menu\Programs\Startup".format(user))

        # Create the program tabs
        self.create_bake_tab()
        self.create_cal_tab()

    # Second argument is required to accept the event, unused here so renamed _
    def toggle_fullscreen(self, _=None):
        """Toggles full screen on and off."""
        self.state = not self.state
        self.attributes("-fullscreen", self.state)
        return "break"

    def end_fullscreen(self, _=None):
        """Exit full screen"""
        self.state = False
        self.attributes("-fullscreen", False)
        return "break"

    def setup_home_frame(self):
        """Sets up the home frame as TK frame that is displayed on launch."""
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
        ttk.Label(device_frame, text="Location", style="Bold.TLabel").grid(row=1, column=3, sticky='ew')
        ttk.Label(device_frame, text="Port", style="Bold.TLabel").grid(row=1, column=5, sticky='ew')
        laser_loc = self.conf_parser.get(constants.DEV_HEADER, "sm125_address")
        laser_port = self.conf_parser.get(constants.DEV_HEADER, "sm125_port")
        switch_loc = self.conf_parser.get(constants.DEV_HEADER, "op_switch_address")
        switch_port = self.conf_parser.get(constants.DEV_HEADER, "op_switch_port")
        temp_loc = self.conf_parser.get(constants.DEV_HEADER, "controller_location")
        oven_loc = self.conf_parser.get(constants.DEV_HEADER, "oven_location")
        switch_conf = [(constants.LASER, laser_loc, laser_port), (constants.SWITCH, switch_loc, switch_port),
                       (constants.TEMP, temp_loc, None), (constants.OVEN, oven_loc, None)]
        for i, dev in enumerate(switch_conf):
            device_frame.grid_rowconfigure(i * 2, pad=20)
            self.device_entry(device_frame, dev[0], dev[1], i + 2, dev[2])
        device_frame.grid(sticky='ew')

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

        self.conn_buttons[dev_text] = lambda: self.conn_dev(loc_ent, port_ent, dev_text)

    def conn_dev(self, loc_ent, port_ent, dev):
        """
        Connects or Disconnects the program to a required device based on the input location params.
        """
        err_specifier = "Unknown error"
        need_conn_warn = False
        need_loc_warn = False
        if True:#self.use_dev:
            # TODO: Fix this to properly warn and try forever
            for _ in range(3):
                try:
                    if dev == constants.TEMP:
                        if self.temp_controller is None:
                            err_specifier = "GPIB address"
                            self.temp_controller = devices.TempController(int(loc_ent.get()), self.manager, self.loop,
                                                                          self.use_dev)
                            self.conf_parser.set(constants.DEV_HEADER, "controller_location", loc_ent.get())
                        else:
                            self.temp_controller.close()
                            self.temp_controller = None
                    elif dev == constants.OVEN:
                        if self.oven is None:
                            err_specifier = "GPIB address"
                            self.oven = devices.Oven(int(loc_ent.get()), self.manager, self.loop, self.use_dev)
                            self.conf_parser.set(constants.DEV_HEADER, "oven_location", loc_ent.get())
                        else:
                            self.oven.close()
                            self.oven = None
                    elif dev == constants.SWITCH:
                        if self.switch is None:
                            err_specifier = "ethernet port"
                            self.switch = devices.OpSwitch(loc_ent.get(), int(port_ent.get()), self.loop, self.use_dev)
                            self.conf_parser.set(constants.DEV_HEADER, "op_switch_address", loc_ent.get())
                            self.conf_parser.set(constants.DEV_HEADER, "op_switch_port", port_ent.get())
                        else:
                            self.switch.close()
                            self.switch = None
                    elif dev == constants.LASER:
                        if self.laser is None:
                            err_specifier = "ethernet port"
                            self.laser = devices.SM125(loc_ent.get(), int(port_ent.get()), self.loop, self.use_dev)
                            self.conf_parser.set(constants.DEV_HEADER, "sm125_address", loc_ent.get())
                            self.conf_parser.set(constants.DEV_HEADER, "sm125_port", port_ent.get())
                        else:
                            self.laser.close()
                            self.laser = None

                    need_conn_warn = False
                    need_loc_warn = False
                    break
                except socket.error:
                    need_conn_warn = True
                    conn_warning(dev)
                except visa.VisaIOError:
                    need_conn_warn = True
                    conn_warning(dev)
                except ValueError:
                    need_loc_warn = True
                    loc_warning(err_specifier)

        if need_conn_warn:
            conn_warning(dev)
        elif need_loc_warn:
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
        if messagebox.askokcancel("Quit", "Are you sure you want to quit?"):
            if self.oven is not None:
                self.oven.close()
            if self.temp_controller is not None:
                self.temp_controller.close()
            if self.switch is not None:
                self.switch.close()
            if self.laser is not None:
                self.laser.close()
            self.destroy()

    def setup_window(self, fiber_path):
        self.title("Kyton FBG UI")
        img = tk.PhotoImage(file=fiber_path)
        self.tk.call('wm', 'iconphoto', self._w, img)

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
            "Treeview" : {"configure": {"foreground" : constants.Colors.WHITE}},
            "Treeview.Heading" : {"configure" : {"foreground" : constants.TEXT_COLOR,
                                                 "font" : {("Helvetica", 12, "bold")}, "sticky": "ew"}},
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
        self.geometry("{0}x{1}+0+0".format(
        self.winfo_screenwidth(), self.winfo_screenheight()))
        #self.attributes("-fullscreen", True)
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
    messagebox.showwarning("Connection Error", "Currently unable to connect to {},".format(dev) +
                           "make sure the device is connected to the computer and the location " +
                           "information is correct.")


def loc_warning(loc_type):
    """Warn the user of an invalid location input."""
    messagebox.showwarning(
        "Invalid Location", "Please import an integer corresponding to the {}.".format(loc_type))


if __name__ == "__main__":
    APP = Application()
    APP.mainloop()
