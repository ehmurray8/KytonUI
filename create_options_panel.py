"""Class sets up the tkinter UI code for the options panel."""

import tkinter as tk

def create_options_grid(app, app_master):
    """Creates the grid for the user to configure options."""

    app_master.title("Kyton Baking")
    app.menu = tk.Menu(app_master, tearoff=0)
    app_master.config(menu=app.menu)
    app.pack(side="top", fill="both", expand=True)

    #Options Grid Init
    app.options_grid.grid_columnconfigure(1, minsize=50)
    app.options_grid.grid_columnconfigure(3, minsize=50)
    row_num = 0


    #Instruments Checkkboxes
    tk.Label(app.options_grid, text="Micron Optics SM125") \
        .grid(row=row_num, sticky="w")
    tk.Checkbutton(app.options_grid, variable=app.sm125_state) \
        .grid(row=row_num, column=2)
    row_num += 1

    tk.Label(app.options_grid, text="Dicon GP700") \
        .grid(row=row_num, sticky="w")
    tk.Checkbutton(app.options_grid, variable=app.gp700_state) \
        .grid(row=row_num, column=2)
    row_num += 1

    tk.Label(app.options_grid, text="340 Controller") \
        .grid(row=row_num, sticky="w")
    tk.Checkbutton(app.options_grid, variable=app.temp340_state) \
        .grid(row=row_num, column=2)
    row_num += 1

    tk.Label(app.options_grid, text="Delta Oven") \
        .grid(row=row_num, sticky="w")
    tk.Checkbutton(app.options_grid, variable=app.delta_oven_state) \
        .grid(row=row_num, column=2)
    row_num += 1


    #Number of points to average entry
    tk.Label(app.options_grid, text="Num points to average: ") \
        .grid(row=row_num, sticky="w")
    app.num_pts_entry.grid(row=row_num, column=2)
    row_num += 1


    #Time intervals entry
    tk.Label(app.options_grid, text="Primary time interval: ") \
        .grid(row=row_num, sticky="w")
    app.prim_time_entry.grid(row=row_num, column=2)
    tk.Label(app.options_grid, text="hours") \
        .grid(row=row_num, column=3)
    row_num += 1

    tk.Label(app.options_grid, text="Secondary time interval: ") \
        .grid(row=row_num, sticky="w")
    app.sec_time_entry.grid(row=row_num, column=2)
    tk.Label(app.options_grid, text="seconds") \
        .grid(row=row_num, column=3)
    row_num += 1


    #File name entry
    tk.Label(app.options_grid, text="File name: ") \
        .grid(row=row_num, sticky="w")
    app.file_entry.grid(row=row_num, column=2)
    row_num += 1


    #Baking setpoint entry
    tk.Label(app.options_grid, text="Baking temp: ") \
        .grid(row=row_num, sticky="w")
    app.baking_temp_entry.grid(row=row_num, column=2)
    row_num += 1


    #Number of Fibers
    tk.Label(app.options_grid, text="Number of fibers for baking: ") \
        .grid(row=row_num, sticky="w")
    app.num_fibers_ent.grid(row=row_num, column=2)
    app.num_fibers_ent.bind("<Return>", app.update_fiber_ents)
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
            self.fibers_sn_arr = []
            self.row_num_sn = 0


            #Init member widgets
            self.options_grid = tk.Frame(self)
            self.options_grid.pack()

            self.num_fibers_ent = tk.Entry(self.options_grid, width=10)
            self.baking_temp_entry = tk.Entry(self.options_grid, width=10)
            self.file_entry = tk.Entry(self.options_grid, width=25)
            self.sec_time_entry = tk.Entry(self.options_grid, width=10)
            self.prim_time_entry = tk.Entry(self.options_grid, width=10)
            self.num_pts_entry = tk.Entry(self.options_grid, width=10)

            #Window setup
            master.title("Kyton Baking")
            self.menu = tk.Menu(master, tearoff=0)
            master.config(menu=self.menu)
            self.pack(side="top", fill="both", expand=True)
            create_options_grid(self, master)
            self.create_fibers_sn_grid()
            self.create_start_btn()

        def update_fiber_ents(self, event):
            """Callback for a change in number of fiber entries."""
            num_str = self.num_fibers_ent.get()
            if is_int(num_str):
                num = int(num_str)
                if num >= 0 and num <= 20:
                    self.config_fiber_ents(num)
                else:
                    self.num_fibers_ent.config(text="1")
                    self.config_fiber_ents(1)
            else:
                self.num_fibers_ent.config(text="1")
                self.config_fiber_ents(1)


        def config_fiber_ents(self, num):
            """Update entries to enter fiber serial numbers."""
            self.start_button.destroy()
            while len(self.fibers_sn_arr) > num:
                print("First...")
                self.fibers_sn_arr.pop().destroy()
                self.row_num_sn -= 1

            while len(self.fibers_sn_arr) < num:
                ent = tk.Entry(self.fibers_sn_grid, width=20)
                ent.grid(row=self.row_num_sn)
                self.row_num_sn += 1

            self.create_start_btn()

        def create_fibers_sn_grid(self):
            """Create the grid for entering fiber serial numbers."""
            self.fibers_sn_grid = tk.Frame(self)
            self.fibers_sn_grid.pack()
            self.fibers_sn_grid.grid_columnconfigure(1, minsize=50)
            self.fibers_sn_grid.grid_columnconfigure(3, minsize=50)


        def create_start_btn(self):
            """Creates the start button in the app."""
            #Start button
            self.start_button = tk.Button(self)
            self.start_button["text"] = "Start"
            #self.confirm_button["command"] = app.start
            self.start_button.pack()


    def is_int(num_str):
        """Checks whether the number is an integer."""
        try:
            int(num_str)
            return True
        except ValueError:
            return False

    ROOT = tk.Tk()
    Application(master=ROOT).mainloop()
