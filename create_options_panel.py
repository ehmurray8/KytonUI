"""Class sets up the tkinter UI code for the options panel."""

import tkinter as tk
import matplotlib
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2TkAgg
from matplotlib.figure import Figure
from numpy import arange, sin, pi
import ui_helper
matplotlib.use('TkAgg')

def create_options_grid(app):
    """Creates the grid for the user to configure options."""

    app_master.title("Kyton Baking")
    app.menu = tk.Menu(app_master, tearoff=0)
    app_master.config(menu=app.menu)
    app.pack(side="top", fill="both", expand=True)

    #Options Grid Init
    app.options_grid.grid_columnconfigure(1, minsize=50)
    app.options_grid.grid_columnconfigure(3, minsize=50)
    row_num = 0


    #Instruments Checkboxes
    app.sm125 = ui_helper.checkbox_entry(app.options_grid,\
                "Micron Optics SM125", row_num)
    row_num += 1

    app.gp700_state = ui_helper.checkbox_entry(app.options_grid,\
                "Dicon GP700", row_num)
    row_num += 1

    app.temp340_state = ui_helper.checkbox_entry(app.options_grid,\
                "340 Controller", row_num)
    row_num += 1

    app.delta_oven_state = ui_helper.checkbox_entry(app.options_grid,\
                "Delta Oven", row_num)
    row_num += 1


    #Number of points to average entry
    app.num_pts = ui_helper.int_entry(app.options_grid, "Num points to average: ",\
                row_num, 10, 1)
    row_num += 1


    #Time intervals entry
    app.prim_time = ui_helper.double_entry(app.options_grid, "Primary time interval: ",\
                row_num, 10, 1.0)
    row_num += 1
    app.sec_time = ui_helper.double_entry(app.options_grid, "Secondary time interval: ",\
                row_num, 10, 1.0)
    row_num += 1


    #File name entry
    app.file_name = ui_helper.string_entry(app.options_grid, "File name: ",\
                row_num, 15, "kyton_out.csv")
    row_num += 1


    #Baking setpoint entry
    app.baking_temp = ui_helper.double_entry(app.options_grid, "Baking temp: ",\
                row_num, 10, 250.0)
    row_num += 1


    #(TEMP) Fiber SN Inputs
    index = 1
    while index <= 20:
        app.sn_ents.append(ui_helper.string_entry(app.options_grid, \
                "Serial Number " + str(index) + ": ", row_num, 20))
        index += 1
        row_num += 1


if __name__ == "__main__":
    class Application(tk.Frame):
        """Main Tkinter window class."""
        def __init__(self, master):
            super().__init__(master)

            #Init member vars
            self.sm125_state = tk.IntVar()
            self.gp700_state = tk.IntVar()
            self.delta_oven_state = tk.IntVar()
            self.temp340_state = tk.IntVar()
            self.sn_ents = []

            #Init member widgets
            self.options_grid = tk.Frame(self)
            self.options_grid.pack()


            self.baking_temp = tk.DoubleVar()
            self.file_name = tk.StringVar()
            self.sec_time = tk.DoubleVar()
            self.prim_time = tk.DoubleVar()
            self.num_pts = tk.IntVar()


            #Window setup
            master.title("Kyton Baking")
            self.menu = tk.Menu(master, tearoff=0)
            master.config(menu=self.menu)
            self.pack(side="top", fill="both", expand=True)
            create_options_grid(self, master)
            self.create_start_btn()
            self.create_graph()


        def create_start_btn(self):
            """Creates the start button in the app."""
            #Start button
            self.start_button = tk.Button(self)
            self.start_button["text"] = "Start"
            self.start_button["command"] = self.start
            self.start_button.pack()

        def start(self):
            ui_helper.print_options(self)

        def create_graph(self):
            fig = Figure(figsize=(5, 4), dpi=100)
            sub = fig.add_subplot(111)
            rng = arange(0.0, 3.0, 0.01)
            y_vals = sin(2*pi*rng)

            sub.plot(rng, y_vals)


            # a tk.DrawingArea
            canvas = FigureCanvasTkAgg(fig, master=ROOT)
            canvas.show()
            canvas.get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH, expand=1)

            toolbar = NavigationToolbar2TkAgg(canvas, ROOT)
            toolbar.update()
            canvas._tkcanvas.pack(side=tk.TOP, fill=tk.BOTH, expand=1)


    ROOT = tk.Tk()
    Application(master=ROOT).mainloop()
