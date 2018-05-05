"""Module contains the main entry point for the Kyton UI."""
from tkinter import messagebox as mbox
import argparse
import configparser
import os
import socket
import sys
from queue import Queue, Empty
import visa

import matplotlib
matplotlib.use("TkAgg")

from fbgui.baking_program import BakingProgram
from fbgui.cal_program import CalProgram
from fbgui import create_excel, constants, devices, reset_config, ui_helper as uh, messages
from fbgui import install
import tkinter as tk
from tkinter import ttk


class Application(tk.Tk):
    """Main Application class."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        install.install()
        reset_config.reset_config()
        parser = argparse.ArgumentParser(description='Run the Kyton program for the correct computer.')
        parser.add_argument('--nodev', action="store_true", help='Use this arg if no devices are available.')
        self.use_dev = True
        cmd_args = parser.parse_args()
        if cmd_args.nodev:
            self.use_dev = False
        self.conf_parser = configparser.ConfigParser()
        self.conf_parser.read(os.path.join("config", "devices.cfg"))

        if self.use_dev:
            try:
                self.manager = visa.ResourceManager()
            except OSError as e:
                if "VISA" in str(e):
                    mbox.showerror("NIVisa not installed",
                                   "Need to install NIVisa to run the program, a copy of NIVisa should be included" +
                                   "in the zip file.")
        else:
            self.manager = None

        self.main_queue = Queue()
        self.thread_map = {}
        self.open_threads = []
        self.graph_threads = []
        self.running = False
        self.running_prog = None
        self.temp_controller = None
        self.oven = None
        self.laser = None
        self.switch = None
        self.is_full_screen = False

        self.controller_location = tk.IntVar()
        self.oven_location = tk.IntVar()
        self.op_switch_address = tk.StringVar()
        self.op_switch_port = tk.IntVar()
        self.sm125_address = tk.StringVar()
        self.sm125_port = tk.IntVar()

        uh.setup_style()
        self.setup_window()

        self.manager = None
        if self.use_dev:
            self.manager = visa.ResourceManager()

        self.main_notebook = ttk.Notebook(self)
        self.main_notebook.enable_traversal()
        self.home_frame = None
        self.device_frame = None
        self.log_view = None
        self.setup_home_frame()
        self.bake_program = None  # type: BakingProgram
        self.cal_program = None   # type: CalProgram
        self.check_queue()

    def check_queue(self):
        while True:
            try:
                msg = self.main_queue.get(timeout=0.1)  # type: messages.Message
                self.log_view.add_msg(msg)
            except Empty:
                break

        self.after(1000, self.check_queue)

    def toggle_full(self, _=None):
        """Toggles full screen on and off."""
        self.is_full_screen = not self.is_full_screen
        self.attributes("-fullscreen", self.is_full_screen)
        return "break"

    def end_full(self, _=None):
        """Exit full screen"""
        self.is_full_screen = False
        self.attributes("-fullscreen", False)
        return "break"

    def setup_home_frame(self):
        """Sets up the home frame as TK frame that is displayed on launch."""
        self.home_frame = ttk.Frame(self.main_notebook)
        self.main_notebook.add(self.home_frame, text="Home")
        self.main_notebook.pack(side="top", fill="both", expand=True)

        hframe = ttk.Frame(self.home_frame)
        hframe.pack()
        self.device_frame = ttk.Frame(hframe)
        col = 0
        self.device_frame.grid_columnconfigure(col, minsize=10)
        col = 2
        while col < 8:
            self.device_frame.grid_columnconfigure(col, minsize=20)
            col += 2
        self.device_frame.grid_columnconfigure(col, minsize=100)
        self.device_frame.grid_rowconfigure(0, minsize=10)

        ttk.Label(self.device_frame, text="Device", style="Bold.TLabel").grid(row=1, column=1, sticky='nsew')
        ttk.Label(self.device_frame, text="Location", style="Bold.TLabel").grid(row=1, column=3, sticky='nsew')
        ttk.Label(self.device_frame, text="Port", style="Bold.TLabel").grid(row=1, column=5, sticky='nsew')
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
            self.device_frame.grid_rowconfigure(i * 2, pad=20)
            uh.device_entry(self.device_frame, dev[0], dev[1], i + 2, dev[2], dev[3], dev[4])
        self.device_frame.pack(anchor=tk.CENTER, expand=True, pady=15)
        self.log_view = messages.LogView(hframe)
        self.log_view.pack(expand=True, fill=tk.BOTH, side=tk.LEFT, anchor=tk.W, padx=25, pady=50)

        create_excel.ExcelTable(hframe, self.main_queue).pack(anchor=tk.E, expand=True, side=tk.LEFT, padx=25)

    def conn_dev(self, dev: str, connect: bool=True, try_once: bool=False, thread_id=None):
        """
        Connects or Disconnects the program to a required device based on the input location params.
        """
        err_specifier = "Unknown error"
        need_conn_warn = False
        need_loc_warn = False

        num = sys.maxsize
        if try_once or thread_id is None:
            num = 1

        for _ in range(num):
            if thread_id is not None and not self.thread_map[thread_id]:
                return
            try:
                if dev == constants.TEMP:
                    if connect:
                        if self.temp_controller is None:
                            err_specifier = "GPIB address"
                            temp_loc = self.controller_location.get()
                            full_loc = "GPIB0::{}::INSTR".format(temp_loc)
                            if self.use_dev and full_loc not in self.manager.list_resources():
                                full_loc = [x for x in self.manager.list_resources() if str(temp_loc) in x]
                                if not len(full_loc):
                                    if try_once:
                                        mbox.showerror("Device Connection Error", "Cannot connect to the temperature "
                                                                                  "controller, check the configured "
                                                                                  "settings on the home screen.")
                                    self.main_queue.put(messages.Message(messages.MessageType.ERROR,
                                                                         "Device Connection Error",
                                                                         "Failed to connect to the temperature "
                                                                         "controller."))
                                    continue
                                else:
                                    self.temp_controller = devices.TempController(full_loc[0], self.manager,
                                                                                  self.use_dev)
                            else:
                                self.temp_controller = devices.TempController(full_loc, self.manager, self.use_dev)
                    else:
                        self.temp_controller.close()
                        self.temp_controller = None
                elif dev == constants.OVEN:
                    if connect:
                        if self.oven is None:
                            err_specifier = "GPIB address"
                            oven_loc = self.oven_location.get()
                            full_loc = "GPIB0::{}::INSTR".format(oven_loc)
                            if self.use_dev and full_loc not in self.manager.list_resources():
                                full_loc = [x for x in self.manager.list_resources() if str(oven_loc) in x]
                                if not len(full_loc):
                                    if try_once:
                                        mbox.showerror("Device Connection Error", "Cannot connect to the oven, "
                                                                                  "check the configured settings on "
                                                                                  "the home screen.")
                                    self.main_queue.put(messages.Message(messages.MessageType.ERROR,
                                                                         "Device Connection Error",
                                                                         "Failed to connect to the oven."))
                                    continue
                                else:
                                    self.oven = devices.Oven(full_loc[0], self.manager, self.use_dev)
                            else:
                                self.oven = devices.Oven(full_loc, self.manager, self.use_dev)
                    else:
                        self.oven.close()
                        self.oven = None
                elif dev == constants.SWITCH:
                    if connect:
                        if self.switch is None:
                            err_specifier = "ethernet port"
                            self.switch = devices.OpSwitch(self.op_switch_address.get(),
                                                           int(self.op_switch_port.get()), self.use_dev)
                    else:
                        self.switch.close()
                        self.switch = None
                elif dev == constants.LASER:
                    if connect:
                        if self.laser is None:
                            err_specifier = "ethernet port"
                            self.laser = devices.SM125(self.sm125_address.get(), int(self.sm125_port.get()),
                                                       self.use_dev)
                    else:
                        self.laser.close()
                        self.laser = None

                need_conn_warn = False
                need_loc_warn = False
                break
            except socket.error:
                need_conn_warn = True
                self.main_queue.put(messages.Message(messages.MessageType.ERROR, "Connection Error",
                                                     "Failed to connect to {}, ".format(dev)))
            except visa.VisaIOError:
                need_conn_warn = True
                self.main_queue.put(messages.Message(messages.MessageType.ERROR, "Connection Error",
                                                     "Failed to connect to {}, ".format(dev)))
            except ValueError:
                need_loc_warn = True
                self.main_queue.put(messages.Message(messages.MessageType.ERROR, "Invalid Location",
                                                     "{} needs an integer input for its {}."
                                                     .format(dev, err_specifier)))

        if need_conn_warn:
            if try_once:
                uh.conn_warning(dev)
        elif need_loc_warn:
            if try_once:
                uh.loc_warning(err_specifier)

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
                if self.manager is not None:
                    self.manager.close()
                for tid in self.open_threads:
                    self.thread_map[tid] = False
                for gid in self.graph_threads:
                    self.thread_map[gid] = False
                self.destroy()
            else:
                self.tkraise()
        else:
            for tid in self.open_threads:
                self.thread_map[tid] = False
            for gid in self.graph_threads:
                self.thread_map[gid] = False
            if self.manager is not None:
                self.manager.close()
            self.destroy()

    def setup_window(self):
        self.title("Kyton FBG UI")
        img = tk.PhotoImage(file=constants.FIBER_PATH)
        self.tk.call('wm', 'iconphoto', self._w, img)
        self.state("zoomed")
        self.protocol("WM_DELETE_WINDOW", self.on_closing)
        self.geometry("{0}x{1}+0+0".format(self.winfo_screenwidth(), self.winfo_screenheight()))
        # Sets up full screen key bindings
        self.bind("<F11>", self.toggle_full)
        self.bind("<Escape>", self.end_full)


if __name__ == "__main__":
    APP = Application()
    APP.bake_program = BakingProgram(APP)
    APP.main_notebook.add(APP.bake_program, text="Bake")
    APP.cal_program = CalProgram(APP)
    APP.main_notebook.add(APP.cal_program, text="Calibration")
    APP.mainloop()
