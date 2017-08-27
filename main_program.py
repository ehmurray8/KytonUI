"""Module contains the main entry point for the Kyton UI."""

import tkinter as tk
from baking_program import BakingPage

LARGE_FONT= ("Verdana", 12)

class Application(tk.Tk):
    """Main Application class."""

    def __init__(self, *args, **kwargs):

        tk.Tk.__init__(self, *args, **kwargs)
        container = tk.Frame(self)

        container.pack(side="top", fill="both", expand=True)

        container.grid_rowconfigure(0, weight=1)
        container.grid_columnconfigure(0, weight=1)

        self.frames = {}

        i = 0
        for page in (StartPage, BakingPage):

            print(i)
            i += 1

            frame = page(container, self)

            self.frames[page] = frame

            frame.grid(row=0, column=0, sticky="nsew")

        self.show_frame(StartPage)


    def show_frame(self, cont):
        """Display a frame on the app."""
        frame = self.frames[cont]
        frame.tkraise()


class StartPage(tk.Frame):

    def __init__(self, parent, controller):
        tk.Frame.__init__(self,parent)
        label = tk.Label(self, text="Kyton UI", font=LARGE_FONT)
        label.pack(pady=10,padx=10)

        button = tk.Button(self, text="Baking Program",
                            command=lambda: controller.show_frame(BakingPage))
        button.pack()

        button2 = tk.Button(self, text="Calibration Program",
                            command=lambda: controller.show_frame(BakingPage))
        button2.pack()


if __name__ == "__main__":
    app = Application()
    app.mainloop()
