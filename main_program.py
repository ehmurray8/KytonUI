"""Module contains the main entry point for the Kyton UI."""

import tkinter as tk
from tkinter import ttk
from tkinter import messagebox
import baking_program
import ui_helper

LARGE_FONT= ("Verdana", 16)

class Application(tk.Tk):
    """Main Application class."""

    def __init__(self, *args, **kwargs):

        tk.Tk.__init__(self, *args, **kwargs)
        container = tk.Frame(self)

        self.title("Kyton UI")
        container.pack(side="top", fill="both", expand=True)

        container.grid_rowconfigure(0, weight=1)
        container.grid_columnconfigure(0, weight=1)

        self.frames = {}

        i = 0
        for page in (StartPage, baking_program.BakingPage, BakingSNSConfig):

            if page == baking_program.BakingPage:
                frame = page(container, self, StartPage)
            else:
                frame = page(container, self)
            self.frames[page] = frame
            frame.grid(row=0, column=0, sticky="nsew")


        self.num_baking_sns = 0
        self.show_frame(StartPage, 300, 300)


    def show_frame(self, cont, width, height):
        """Display a frame on the app."""
        frame = self.frames[cont]
        ui_helper.open_center(width, height, self)
        frame.tkraise()


    def start_bake(self, inpt, baking_page):
        """Starts the baking program."""
        if inpt is not None:
            number = inpt.get()
            valid = True
            try:
                self.num_baking_sns = int(number)
            except ValueError:
                valid = False
                messagebox.showwarning("Invalid Input", "Please input an integer.")

        
        height = 330 + (self.num_baking_sns * 10)
        height += int(self.num_baking_sns / 3) * 30
        baking_page.clear_frame()
        baking_page.create_options(self.num_baking_sns)
        baking_page.create_menu(self)
        self.title("Kyton Baking")
        self.show_frame(baking_program.BakingPage, 475, height)

    def start_baking_program(self):
        if not self.frames[baking_program.BakingPage].running:
            self.show_frame(BakingSNSConfig, 275, 125)
        else:
            self.start_bake(None, self.frames[baking_program.BakingPage])


class StartPage(tk.Frame):

    def __init__(self, parent, controller):
        self.controller = controller
        tk.Frame.__init__(self,parent)
        label = tk.Label(self, text="Kyton Programs", font=LARGE_FONT)
        label.pack(pady=(10, 50))

        button = tk.Button(self, text="Baking Program",
                            command=controller.start_baking_program)
        button.pack(pady=(0, 40))

        button2 = tk.Button(self, text="Calibration Program")#,
                            #command=lambda: controller.show_frame(BakingPage, ))
        button2.pack()

    

class BakingSNSConfig(tk.Frame):

    def __init__(self, parent, controller):
        """Launches Dialog box to input number of fibers."""
        tk.Frame.__init__(self, parent)

        tk.Label(self, text="How many fibers will be used for baking? ").\
                pack(side="top", expand=True, padx=10, pady=5)
        self.inpt = ttk.Entry(self, width=10, justify="center")
        self.inpt.pack(side="top", padx=10, pady=5, expand=True)
        self.inpt.focus()
        ttk.Button(self, text="Start Baking", command=lambda: controller.start_bake(self.inpt,
                controller.frames[baking_program.BakingPage])).pack(side="top", expand=True, padx=10, pady=5)
        #controller.title("Baking Settings")
        controller.bind('<Return>', lambda x: controller.start_bake(self.inpt, controller.frames[baking_program.BakingPage]))
        #ui_helper.open_center(275, 125, controller)


if __name__ == "__main__":
    app = Application()
    app.mainloop()
