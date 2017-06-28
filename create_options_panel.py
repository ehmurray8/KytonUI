import tkinter as tk

def create_options_grid(app, app_master):

    app_master.title("Kyton Baking")
    app.menu = tk.Menu(app_master, tearoff=0)
    app_master.config(menu=app.menu)
    app.sm125_state = tk.IntVar()
    app.gp700_state = tk.IntVar()
    app.delta_oven_state = tk.IntVar()
    app.temp340_state = tk.IntVar()
    app.pack(side="top", fill="both", expand=True)

    #Options Grid Init
    options_grid = tk.Frame(app)
    options_grid.pack()
    options_grid.grid_columnconfigure(1, minsize=50)
    options_grid.grid_columnconfigure(3, minsize=50)


    #Instruments Checkkboxes
    sm125_lbl = tk.Label(options_grid)
    sm125_lbl["text"] = "Micron Optics SM125"
    sm125_lbl.grid(row=0, sticky="w")
    sm125_select = tk.Checkbutton(options_grid, variable=app.sm125_state)
    sm125_select.grid(row=0, column=2)

    gp700_lbl = tk.Label(options_grid)
    gp700_lbl["text"] = "Dicon GP700"
    gp700_lbl.grid(row=1, sticky="w")
    gp700_select = tk.Checkbutton(options_grid, variable=app.gp700_state)
    gp700_select.grid(row=1, column=2)

    temp340_lbl = tk.Label(options_grid)
    temp340_lbl["text"] = "340 Controller"
    temp340_lbl.grid(row=2, sticky="w")
    temp340_select = tk.Checkbutton(options_grid, variable=app.temp340_state)
    temp340_select.grid(row=2, column=2)

    delta_oven_lbl = tk.Label(options_grid)
    delta_oven_lbl["text"] = "Delta Oven"
    delta_oven_lbl.grid(row=3, sticky="w")
    delta_oven_select = tk.Checkbutton(options_grid, variable=app.delta_oven_state)
    delta_oven_select.grid(row=3, column=2)


    #Number of points to average entry
    num_pts_lbl = tk.Label(options_grid, text="Num points to average: ")
    num_pts_lbl.grid(row=4, sticky="w")
    app.num_pts_entry = tk.Entry(options_grid, width=10)
    app.num_pts_entry.grid(row=4, column=2)


    #Time intervals entry
    prim_time_lbl = tk.Label(options_grid, text="Primary time interval: ")
    prim_time_lbl.grid(row=5, sticky="w")
    app.prim_time_entry = tk.Entry(options_grid, width=10)
    app.prim_time_entry.grid(row=5, column=2)
    prim_time_post_lbl = tk.Label(options_grid, text="hours")
    prim_time_post_lbl.grid(row=5, column=3)

    sec_time_lbl = tk.Label(options_grid, text="Secondary time interval: ")
    sec_time_lbl.grid(row=6, sticky="w")
    app.sec_time_entry = tk.Entry(options_grid, width=10)
    app.sec_time_entry.grid(row=6, column=2)
    sec_time_post_lbl = tk.Label(options_grid, text="seconds")
    sec_time_post_lbl.grid(row=6, column=3)


    #File name entry
    file_lbl = tk.Label(options_grid, text="File name: ")
    file_lbl.grid(row=7, sticky="w")
    app.file_entry = tk.Entry(options_grid, width=25)
    app.file_entry.grid(row=7, column=2)


    #Baking setpoint entry
    baking_temp_lbl = tk.Label(options_grid, text="Baking temp: ")
    baking_temp_lbl.grid(row=8, sticky="w")
    app.baking_temp_entry = tk.Entry(options_grid, width=10)
    app.baking_temp_entry.grid(row=8, column=2)


    #Start button
    app.confirm_button = tk.Button(app)
    app.confirm_button["text"] = "Start"
    self.confirm_button["command"] = app.start
    app.confirm_button.pack()

if __name__ == "__main__":
    class Application(tk.Frame):
        def __init__(self, master):
            super().__init__(master)

            master.title("Kyton Baking")
            self.menu = tk.Menu(master, tearoff=0)
            master.config(menu=self.menu)
            self.sm125_state = tk.IntVar()
            self.gp700_state = tk.IntVar()
            self.delta_oven_state = tk.IntVar()
            self.temp340_state = tk.IntVar()
            self.pack(side="top", fill="both", expand=True)
            create_options_grid(self)


    root = tk.Tk()
    application = Application(master=root)
    application.mainloop()