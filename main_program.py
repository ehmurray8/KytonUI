"""Module contains the main entry point for the Kyton UI."""

# pylint: disable=import-error, relative-import
from tkinter import ttk
from tkinter import messagebox
import tkinter as tk 
from baking_program import BakingPage
from cal_program import CalPage
import ui_helper

LARGE_FONT = ("Verdana", 16)


class Application(tk.Tk):
    """Main Application class."""

    def __init__(self, *args, **kwargs):
        # pylint: disable=missing-super-argument
        super().__init__(*args, **kwargs)
        container = tk.Frame(self)

        self.title("Kyton UI")
        container.pack(side="top", fill="both", expand=True)

        container.grid_rowconfigure(0, weight=1)
        container.grid_columnconfigure(0, weight=1)

        self.frames = {}

        for page in (StartPage, BakingPage, BakingSNSConfig,
                     CalPage, CalSNSConfig):
            if page == BakingPage or page == CalPage:
                frame = page(container, self, StartPage)
            else:
                frame = page(container, self)

            self.frames[page] = frame
            frame.grid(row=0, column=0, sticky="nsew")

        self.num_baking_sns = 0
        self.num_cal_sns = 0
        self.show_frame(StartPage, 300, 300)

    def show_frame(self, cont, width, height):
        """Display a frame on the app."""
        frame = self.frames[cont]
        ui_helper.open_center(width, height, self)
        frame.tkraise()

    def start_bake(self, inpt, baking_page):
        """Starts the baking program."""

        valid = True
        if inpt is not None:
            number = inpt.get()
            try:
                self.num_baking_sns = int(number)
            except ValueError:
                valid = False
                messagebox.showwarning("Invalid Input",
                                       "Please input an integer.")

        if valid:
            height = 330 + (self.num_baking_sns * 10)
            height += int(self.num_baking_sns / 3) * 30
            if inpt is not None:
                baking_page.clear_frame()
                baking_page.header = ttk.Label(baking_page.main_frame,
                                               text="Configure Baking",
                                               font=LARGE_FONT)
                baking_page.header.pack(pady=10)
                baking_page.create_options(self.num_baking_sns)
            baking_page.create_menu(self)
            self.title("Kyton Baking")
            self.unbind("<Return>")
            self.show_frame(BakingPage, 700, height)

    def start_baking_program(self):
        """Launches the baking program."""
        if not self.frames[BakingPage].running:
            self.title("Baking Settings")
            self.bind('<Return>', lambda x: self.start_bake(
                BakingSNSConfig.inpt, self.frames[BakingPage]))
            self.show_frame(BakingSNSConfig, 300, 125)
            BakingSNSConfig.inpt.focus()
        else:
            self.start_bake(None, self.frames[BakingPage])

    def start_cal(self, inpt, cal_page):
        """Starts the baking program."""
        valid = True
        if inpt is not None:
            number = inpt.get()
            try:
                self.num_cal_sns = int(number)
            except ValueError:
                valid = False
                messagebox.showwarning("Invalid Input",
                                       "Please input an integer.")

        if valid:
            height = 470 + (self.num_cal_sns * 10)
            height += int(self.num_cal_sns / 3) * 30
            if inpt is not None:
                cal_page.clear_frame()
                cal_page.header = ttk.Label(cal_page.main_frame,
                                            text="Configure Calibration",
                                            font=LARGE_FONT)
                cal_page.header.pack(pady=10)
                cal_page.create_options(self.num_cal_sns)
            cal_page.create_menu(self)
            self.title("Kyton Calibration")
            self.unbind("<Return>")
            self.show_frame(CalPage, 700, height)

    def start_cal_program(self):
        """Launches the calibration program."""
        if not self.frames[CalPage].running:
            self.title("Calibration Settings")
            self.bind("<Return>", lambda x: self.start_cal(
                CalSNSConfig.inpt, self.frames[CalPage]))
            self.show_frame(CalSNSConfig, 300, 125)
            CalSNSConfig.inpt.focus()
        else:
            self.start_cal(None, self.frames[CalPage])

# pylint: disable=too-few-public-methods


class StartPage(tk.Frame):
    """Creates the StartPage for the program."""

    def __init__(self, parent, controller):
        self.controller = controller
        tk.Frame.__init__(self, parent)
        label = tk.Label(self, text="Kyton Programs", font=LARGE_FONT)
        label.pack(pady=(10, 50))

        button = tk.Button(self, text="Baking Program",
                           command=controller.start_baking_program)
        button.pack(pady=(0, 40))

        button2 = tk.Button(self, text="Calibration Program",
                            command=controller.start_cal_program)
        button2.pack()


class BakingSNSConfig(tk.Frame):
    """Creates the number of serial number dialog for the Cal page."""

    def __init__(self, parent, controller):
        """Launches Dialog box to input number of fibers."""
        tk.Frame.__init__(self, parent)

        tk.Label(self, text="How many fibers will be used for baking? "). \
            pack(side="top", expand=True, padx=10, pady=5)
        BakingSNSConfig.inpt = ttk.Entry(self, width=10, justify="center")
        BakingSNSConfig.inpt.pack(side="top", padx=10, pady=5, expand=True)
        start_bake_btn = ttk.Button(self, text="Start Baking",
                                    command=lambda: controller.start_bake(
                                        BakingSNSConfig.inpt,
                                        controller.frames[BakingPage]))
        start_bake_btn.pack(side="top", expand=True, padx=10, pady=5)


class CalSNSConfig(tk.Frame):
    """Creates the number of serial number dialog for the Bake page."""

    def __init__(self, parent, controller):
        """Launches Dialog box to input number of fibers."""
        tk.Frame.__init__(self, parent)

        tk.Label(self, text="How many fibers will be used for calibration? ").\
            pack(side="top", expand=True, padx=10, pady=5)
        CalSNSConfig.inpt = ttk.Entry(self, width=10, justify="center")
        CalSNSConfig.inpt.pack(side="top", padx=10, pady=5, expand=True)
        start_cal_btn = ttk.Button(self, text="Start Calibration",
                                   command=lambda: controller.start_cal(
                                       CalSNSConfig.inpt,
                                       controller.frames
                                       [CalPage]))
        start_cal_btn.pack(side="top", expand=True, padx=10, pady=5)


if __name__ == "__main__":
    APP = Application()
    APP.mainloop()
