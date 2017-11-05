"""
Abstract class defines common functionality between calibration
program and baking program.
"""

# pylint: disable=import-error, relative-import
import sys
import socket
import os
from tkinter import ttk, messagebox
import queue
import tkinter as tk
import pyvisa as visa

import options_frame
import file_helper as fh
import graphing_helper as gh
import ui_helper
import devices

LARGE_FONT = ("Verdana", 13)

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
        else:
            self.title = "Configre Calibration"
            self.config_id = fh.CAL_SECTION
            self.options = options_frame.CAL
            self.in_prog_msg = "Calibrating..."


class Page(tk.Frame):  # pylint: disable=too-many-instance-attributes
    """Definition of the abstract program page."""

    def __init__(self, parent, master, start_page, program_type):
        super().__init__(parent)  # pylint: disable=missing-super-argument

        self.master = master
        self.master.protocol("WM_DELETE_WINDOW", self.on_closing)
        self.program_type = program_type
        self.oven = None
        self.op_switch = None
        self.sm125 = None
        self.channels = [[], [], [], []]
        self.switches = [[], [], [], []]
        self.snums = []
        self.stable_count = 0
        self.running = False
        self.cancel_run = False
        self.start_page = start_page
        self.chan_error_been_warned = False
        self.options = None
        self.start_btn = None
        self.data_pts = {}

        #self.main_frame = tk.Frame(self)
        #self.header = ttk.Label(self.main_frame, text=self.program_type.title,
        #                        font=LARGE_FONT)
        #self.header.pack(pady=10)

    def clear_frame(self):
        """Clears the main frame."""
        self.main_frame.destroy()
        self.main_frame = tk.Frame(self)
        self.main_frame.pack(expand=1, fill=tk.BOTH)

    def home(self):
        """Return to StartPage."""
        if self.running:
            tk.messagebox.showwarning("Warning Program is Running",
                                      " ".join(["Cannot return to the home screen while the",
                                                "program is running. Please pause the program",
                                                "to continue."]))
        else:
            self.menu = tk.Menu(self.master, tearoff=0)
            self.master.config(menu=self.menu)
            self.master.show_frame(self.start_page, 300, 300)

    def create_options(self, num_sns):
        """Creates the options panel for the main frame."""
        self.options = options_frame.OptionsPanel(self.main_frame, num_sns,
                                                  self.program_type.options)
        self.start_btn = self.options.create_start_btn(self.start)
        self.options.pack()

    def create_excel(self):
        """Creates excel file."""
        fh.create_excel_file(self.options.file_nme.get())

    def start(self, can_start=False):
        """Starts the recording process."""
        delayed_prog = None

        if not can_start:
            if not self.running:
                conn_fails = []
                if len(sys.argv) > 1 and sys.argv[1] == "-k":
                    self.load_devices(conn_fails)

                for chan, snum, pos in zip(self.options.chan_nums,
                                           self.options.sn_ents,
                                           self.options.switch_positions):
                    if snum.get() != "" and snum.get() not in self.snums:
                        self.snums.append(snum.get())
                        self.channels[chan.get() - 1].append(snum.get())
                        self.switches[chan.get() - 1].append(pos.get())

                if len(conn_fails) == 0:
                    self.running = True
                    self.start_btn.configure(text="Pause")
                    self.header.configure(text=self.program_type.in_prog_msg)
                    ui_helper.lock_widgets(self.options)
                else:
                    need_comma = False
                    conn_str = "Failed to connect to: "
                    for dev in conn_fails:
                        if need_comma:
                            conn_str += ", "
                            need_comma = True
                        conn_str += dev
                    conn_str += "."
                    messagebox.showwarning(
                        "Device Connection Failure", conn_str)

                delayed_prog = self.master.after(int(self.options.delay.get() *
                                                     1000 * 60 * 60 + .5), lambda: self.start(True))
            else:
                if delayed_prog is not None:
                    self.master.after_cancel(delayed_prog)
                    delayed_prog = None
                self.pause_program()
        else:
            self.program_loop()

    def pause_program(self):
        """Pauses the program."""
        self.start_btn.configure(text="Start")
        self.header.configure(text=self.program_type.title)
        ui_helper.unlock_widgets(self.options)
        self.running = False
        self.stable_count = 0
        self.snums = []
        self.channels = [[], [], [], []]
        self.switches = [[], [], [], []]
        if self.oven is not None:
            self.oven.close()
            self.oven = None
        if self.temp_controller is not None:
            self.temp_controller.close()
            self.temp_controller = None
        if self.sm125 is not None:
            self.sm125.close()
            self.sm125 = None
        if self.op_switch is not None:
            self.op_switch.close()
            self.op_switch = None

    def on_closing(self):
        """Stops the user from closing if the program is running."""
        if self.running:
            if messagebox.askyesno("Quit",
                                   "Program is currently running. Are you sure you want to quit?"):
                self.master.destroy()
            else:
                self.master.tkraise()
        else:
            self.master.destroy()
