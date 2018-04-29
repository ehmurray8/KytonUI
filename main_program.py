"""Module contains the main entry point for the Kyton UI."""

import argparse
import configparser
import os
import sys
import socket
from queue import Queue, Empty
from tkinter import ttk
from shutil import copy2
import matplotlib
import visa
import constants
matplotlib.use("TkAgg")

from baking_program import BakingProgram
from cal_program import CalProgram
import devices
import create_excel
import ui_helper as uh
from reset_config import reset_config
from tkinter import messagebox as mbox
import tkinter as tk


class Application(tk.Tk):
    """Main Application class."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        reset_config()

        parser = argparse.ArgumentParser(description='Run the Kyton program for the correct computer.')
        parser.add_argument('--nodev', action="store_true", help='Use this arg if no devices are available.')
        self.use_dev = True
        cmd_args = parser.parse_args()
        if cmd_args.nodev:
            self.use_dev = False
        self.conf_parser = configparser.ConfigParser()
        self.conf_parser.read(os.path.join("config", "devices.cfg"))

        site_packs = [s for s in sys.path if 'site-packages' in s][0]
        copy2(constants.MPL_STYLE_PATH, os.path.join(site_packs, "matplotlib", "mpl-data", "stylelib"))
        copy2(constants.PLAY_PATH, os.path.join(site_packs, "matplotlib", "mpl-data", "images"))
        copy2(constants.PAUSE_PATH, os.path.join(site_packs, "matplotlib", "mpl-data", "images"))

        self.main_queue = Queue()
        self.thread_map = {}
        self.open_threads = []
        self.graph_threads = []
        self.running = False
        self.running_prog = None
        self.temp_controller: devices.TempController = None
        self.oven: devices.Oven = None
        self.laser: devices.SM125 = None
        self.switch: devices.OpSwitch = None
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
        self.home_frame: ttk.Frame = None
        self.device_frame: ttk.Frame = None
        self.setup_home_frame()
        self.bake_program = BakingProgram(self)
        self.main_notebook.add(self.bake_program, text="Bake")
        self.cal_program = CalProgram(self)
        self.main_notebook.add(self.cal_program, text="Calibration")

    def check_queue(self):
        while True:
            msg = ""
            try:
                msg = self.main_queue.get(timeout=0.1)
            except Empty:
                break
            # Handle message

        self.after(10000, self.check_queue)

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
        create_excel.Table(hframe).pack(pady=175, anchor=tk.S, expand=True)

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
                            full_loc = "GPIB0::{}::INSTR".format(temp_loc)
                            if self.use_dev and full_loc not in self.manager.list_resources():
                                continue
                            else:
                                self.temp_controller = devices.TempController(int(temp_loc), self.manager, self.use_dev)
                    else:
                        self.temp_controller.close()
                        self.temp_controller = None
                elif dev == constants.OVEN:
                    if connect:
                        if self.oven is None:
                            err_specifier = "GPIB address"
                            oven_loc = self.conf_parser.get(constants.DEV_HEADER, "oven_location")
                            full_loc = "GPIB0::{}::INSTR".format(oven_loc)
                            if full_loc not in self.manager.list_resources():
                                continue
                            else:
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
                uh.conn_warning(dev)
        elif need_loc_warn:
            if try_once:
                uh.loc_warning(err_specifier)

    def on_closing(self):
        for tid in self.open_threads:
            self.thread_map[tid] = False
        for gid in self.graph_threads:
            self.thread_map[gid] = False

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
    APP.mainloop()
