"""Class sets up the tkinter UI code for the options panel."""

import tkinter as tk
import ui_helper


class OptionsPanel(tk.Frame):
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
        self.init_time = tk.DoubleVar()
        self.init_duration = tk.DoubleVar()
        self.prim_time = tk.DoubleVar()
        self.num_pts = tk.IntVar()

        self.create_options_grid()
        self.start_button = tk.Button(self)


    def create_options_grid(self):
        """Creates the grid for the user to configure options."""

        self.pack(side="top", fill="both", expand=True)

        #Options Grid Init
        self.options_grid.grid_columnconfigure(1, minsize=50)
        self.options_grid.grid_columnconfigure(3, minsize=50)
        row_num = 0


        #Instruments Checkboxes
        self.sm125_state = ui_helper.checkbox_entry(self.options_grid,\
                    "Micron Optics SM125", row_num)
        row_num += 1

        self.gp700_state = ui_helper.checkbox_entry(self.options_grid,\
                    "Dicon GP700", row_num, False)
        row_num += 1

        self.temp340_state = ui_helper.checkbox_entry(self.options_grid,\
                    "340 Controller", row_num)
        row_num += 1

        self.delta_oven_state = ui_helper.checkbox_entry(self.options_grid,\
                    "Delta Oven", row_num)
        row_num += 1


        #Number of points to average entry
        self.num_pts = ui_helper.int_entry(self.options_grid, "Num points to average: ",\
                    row_num, 10, 5)
        row_num += 1


        #Time intervals entry
        self.init_time = ui_helper.time_entry(self.options_grid, "Initial time interval: ",\
                    row_num, 10, "seconds", 15.0)
        row_num += 1

        self.init_duration = ui_helper.time_entry(self.options_grid, "Initial interval duration: ",\
                    row_num, 10, "minutes", 5.0)
        row_num += 1

        self.prim_time = ui_helper.time_entry(self.options_grid, "Primary time interval: ",\
                    row_num, 10, "minutes", 1.0)
        row_num += 1


        #File name entry
        self.file_name = ui_helper.string_entry(self.options_grid, "File name: ",\
                    row_num, 15, "kyton_out.csv")
        row_num += 1


        #Baking setpoint entry
        self.baking_temp = ui_helper.double_entry(self.options_grid, "Baking temp: ",\
                    row_num, 10, 250.0)
        row_num += 1


        #(TEMP) Fiber SN Inputs
        index = 1
        while index <= 4:
            self.sn_ents.append(ui_helper.string_entry(self.options_grid, \
                    "Serial Number " + str(index) + ": ", row_num, 20, \
		    "Fiber " + str(index)))
            index += 1
            row_num += 1

    def create_start_btn(self, start):
        """Creates the start button in the app."""
        #Start button
        self.start_button["text"] = "Start"
        self.start_button["command"] = start
        self.start_button.pack()


if __name__ == "__main__":
    ROOT = tk.Tk()
    OptionsPanel(ROOT).mainloop()
