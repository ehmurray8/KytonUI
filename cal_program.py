"""Calibratin Program for Kyton UI."""

import tkinter as tk
from tkinter import ttk

LARGE_FONT = ("Verdana", 13)

class CalPage(tk.Frame): # pylint: disable=too-many-ancestors, too-many-instance-attributes
    """Class containing the main tkinter application."""

    def __init__(self, parent, master, start_page):
        """Constructs the app."""
        tk.Frame.__init__(self, parent)

        self.controller = None
        self.oven = None
        self.gp700 = None
        self.sm125 = None
        self.channels = [[], [], [], []]
        self.switches = []
        self.snums = []

        self.main_frame = tk.Frame(self)

        self.header = ttk.Label(self.main_frame, text="Configure Calibration", font=LARGE_FONT)
        self.header.pack(pady=10)

        self.stable_count = 0

        self.menu = tk.Menu(master, tearoff=0)

        self.running = False
        self.cancel_bake = False
        self.start_page = start_page


    def clear_frame(self):
        """Clear the main frame, and construct a new blank main frame."""
        self.main_frame.destroy()
        self.main_frame = tk.Frame(self)
        self.main_frame.pack(expand=1, fill=tk.BOTH)

    def home(self, master):
        """Return to StartPage."""
        self.menu = tk.Menu(master, tearoff=0)
        master.config(menu=self.menu)
        master.show_frame(self.start_page, 300, 300)
