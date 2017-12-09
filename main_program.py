"""Module contains the main entry point for the Kyton UI."""

# pylint: disable=too-many-arguments, too-many-branches
# pylint: disable=too-many-instance-attributes
# pylint: disable=import-error, relative-import

#import queue
import socket
import argparse
from tkinter import ttk
import platform
import matplotlib
import configparser

matplotlib.use("TkAgg")
from matplotlib import style
from tkinter import messagebox
import tkinter as tk
if platform.system() == "Linux":
    from ttkthemes import ThemedStyle
import devices
import visa
from baking_program import BakingPage
from cal_program import CalPage
import colors
style.use('kyton')


OVEN = "Delta Oven"
LASER = "Micron Optics SM125"
SWITCH = "Optical Switch"
TEMP = "LSC Temperature Controller"
CPARSER = configparser.SafeConfigParser()
CPARSER.read("devices.cfg")
HEADER = "Devices"


class Application(tk.Tk):
    """Main Application class."""

    def __init__(self, *args, **kwargs):
        # pylint: disable=missing-super-argument
        super().__init__(*args, **kwargs)

        # Created for development purposes --nodev runs on a computer w/o
        # proper instruments connected
        parser = argparse.ArgumentParser(
            description='Run the Kyton program for the correct computer.')
        parser.add_argument('--nodev', action="store_true",
                            help='Use this arg if no devices are available.')
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
            "TEntry": {"configure": {"font": ('Helvetica', 14)},
                       "map":       {"fieldbackground": [("active", colors.ENTRY_COLOR),
                                                         ("disabled", colors.BLACK)],
                                     "foreground": [("active", "black"),
                                                    ("disabled", colors.TEXT_COLOR)]}},
            "TNotebook": {"configure": {"tabmargins": [10, 10, 10, 2]}},
            "TCheckbutton": {"configre": {"height": 40, "width": 40}},
            "TNotebook.Tab": {
                "configure": {"padding": [10, 4], "font": ('Helvetica', 18),
                              "background": colors.TAB_COLOR},
                "map":       {"background": [("selected", colors.TABS_COLOR)],
                              "font": [("selected", ('Helvetica', 18, "bold"))],
                              "expand": [("selected", [1, 1, 1, 0])]}}})

        # Used exclusively for development purposes
        if platform.system() == "Linux":
            self.style.set_theme("main")
        else:
            self.style.theme_use("main")

        self.main_notebook = ttk.Notebook()
        self.main_notebook.enable_traversal()

        self.home_frame = ttk.Frame()
        self.main_notebook.add(self.home_frame, text="Home")
        self.main_notebook.pack(side="top", fill="both", expand=True)
        self.running_prog = None

        self.device_widgets = []
        #self.main_queue = queue.Queue()

        if self.use_dev:
            self.manager = visa.ResourceManager()

        self.bake = None
        self.cal = None
        self.running = False

        self.temp_controller = None
        self.oven = None
        self.laser = None
        self.switch = None

        self.conn_buttons = []

        self.setup_home_frame()

        # Make the app fullscreen
        self.geometry("{0}x{1}+0+0".format(
            self.winfo_screenwidth(), self.winfo_screenheight()))
        self.attributes("-fullscreen", True)
        self.state = True

        # Sets up full screen key bindings
        self.bind("<F11>", self.toggle_fullscreen)
        self.bind("<Escape>", self.end_fullscreen)

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

        ttk.Label(device_frame, text="Device", style="Bold.TLabel").grid(
            row=1, column=1, sticky='ew')
        ttk.Label(device_frame, text="Location", style="Bold.TLabel").grid(
            row=1, column=3, sticky='ew')
        ttk.Label(device_frame, text="Port", style="Bold.TLabel").grid(
            row=1, column=5, sticky='ew')
        ttk.Label(device_frame, text="Connection Status", style="Bold.TLabel").grid(
            row=1, column=7, sticky='ew')
        laser_loc = CPARSER.get(HEADER, "sm125_address")
        laser_port = CPARSER.get(HEADER, "sm125_port")
        switch_loc = CPARSER.get(HEADER, "op_switch_address")
        switch_port = CPARSER.get(HEADER, "op_switch_port")
        temp_loc = CPARSER.get(HEADER, "controller_location")
        oven_loc = CPARSER.get(HEADER, "oven_location")
        switch_conf = [(LASER, laser_loc, laser_port), (SWITCH, switch_loc, switch_port),
                       (TEMP, temp_loc, None), (OVEN, oven_loc, None)]
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

        conn_butt = ttk.Button(container, text="Connect",
                               command=lambda: self.conn_dev(loc_ent, port_ent, dev_text,
                                                             conn_butt))
        conn_butt.grid(row=row, column=7, sticky='ew')
        self.conn_buttons.append(conn_butt)
        #self.device_widgets.append((loc_ent, port_ent, conn_butt))

    def conn_dev(self, loc_ent, port_ent, dev, button):
        """
        Connects or Disconnects the program to a required device based on the input location params.
        """
        connect = False
        if self.use_dev:
            try:
                if dev == TEMP:
                    if self.temp_controller is None:
                        err_specifier = "GPIB address"
                        self.temp_controller = devices.TempController(int(loc_ent.get()),
                                                                      self.manager)
                        CPARSER.set(HEADER, "controller_location", loc_ent.get())
                        connect = True
                    else:
                        self.temp_controller.close()
                        self.temp_controller = None
                elif dev == OVEN:
                    if self.oven is None:
                        err_specifier = "GPIB address"
                        self.oven = devices.Oven(int(loc_ent.get()), self.manager)
                        CPARSER.set(HEADER, "oven_location", loc_ent.get())
                        connect = True
                    else:
                        self.oven.close()
                        self.oven = None
                elif dev == SWITCH:
                    if self.switch is None:
                        err_specifier = "ethernet port"
                        self.switch = devices.OpSwitch(loc_ent.get(), int(port_ent.get()))
                        CPARSER.set(HEADER, "op_switch_address", loc_ent.get())
                        CPARSER.set(HEADER, "op_switch_port", port_ent.get())
                        connect = True
                    else:
                        self.switch.close()
                        self.switch = None
                elif dev == LASER:
                    if self.laser is None:
                        err_specifier = "ethernet port"
                        self.laser = devices.SM125(loc_ent.get(), int(port_ent.get()))
                        CPARSER.set(HEADER, "sm125_address", loc_ent.get())
                        CPARSER.set(HEADER, "sm125_port", port_ent.get())
                        connect = True
                    else:
                        self.laser.close()
                        self.laser = None
            except socket.error:
                conn_warning(dev)
            except visa.VisaIOError:
                conn_warning(dev)
            except ValueError:
                loc_warning(err_specifier)

        if connect:
            button['text'] = "Disconnect"
        else:
            button['text'] = "Connect"

    def create_bake_tab(self):
        """Create a tab used for a baking run."""
        self.bake = BakingPage(self)
        self.main_notebook.add(self.bake, text="Bake")

    def create_cal_tab(self):
        """Create a tab used for a calibration run."""
        self.cal = CalPage(self)
        self.main_notebook.add(self.cal, text="Calibration")

    # def tkloop(self):
    #    """Loop for threaded processes."""
    #    try:
    #        while True:
    #            func, args, kwargs = self.main_queue.get_nowait()
    #            func(*args, **kwargs)
    #    except queue.Empty:
    #        pass
    #    self.after(200, self.tkloop)


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
    # APP.tkloop()
    APP.mainloop()
