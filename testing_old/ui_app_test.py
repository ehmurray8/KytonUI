import tkinter as tk

import matplotlib
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

matplotlib.use('TkAgg')


class Application(tk.Frame):
    def __init__(self, master=None):
        super().__init__(master)
        self.grid()

        # SETTINGS
        self.controller_text = self.string_entry("Controller location:", 'GPIB::12::INSTR', 0)
        self.oven_text = self.string_entry("Oven location:", 'GPIB0::27::INSTR', 1)
        self.interrogator_ip_text = self.string_entry("Interrogator IP:", '10.0.0.122', 2)
        self.interrogator_port_text = self.int_entry("Interrogator port:", 50000, 3)
        self.drift_number_text = self.int_entry("# temps for drift:", 5, 4)
        self.wait_time_text = self.double_entry("Wait time b/w points:", 2.0, 5)
        self.set_point_list_text = self.string_entry("Set-points to check:", "[50.0, 100.0, 150.0]", 6)
        self.dwell_text = self.int_entry("Dwell time:", 8, 7)
        self.ranges_text = self.string_entry("Ranges:",
                                             "[[20, 20.0, 50], [50, 15.0, 50], [100, 20.0, 50], [1000, 20.0, 50]]", 8)
        self.run_button = tk.Button(self, text="Button", command=self.activate_button)
        self.run_button.grid(row=9, column=0)

        # PLOTTING
        self.fig = plt.figure(1)
        plt.ion()
        self.t = np.arange(0.0, 3.0, 0.01)
        self.s = np.sin(np.pi * self.t)
        plt.plot(self.t, self.s)

        canvas = FigureCanvasTkAgg(self.fig, master=root)
        plot_widget = canvas.get_tk_widget()

        plot_widget.grid(row=0, column=1)
        tk.Button(root, text="Re-plot", command=self.update_plot).grid(row=1, column=1)

    def gather_settings(self):
        return self.controller_text.get(), \
               self.oven_text.get(), \
               self.interrogator_ip_text.get(), \
               self.interrogator_port_text.get(), \
               self.drift_number_text.get(), \
               self.wait_time_text.get(), \
               self.set_point_list_text.get(), \
               self.dwell_text.get(), \
               self.ranges_text.get()

    def string_entry(self, label_text, default_str, row):
        text_var = tk.StringVar()
        tk.Label(self, text=label_text).grid(row=row, column=0, sticky='W')
        tk.Entry(self, textvariable=text_var).grid(row=row, column=1, sticky='W')
        text_var.set(default_str)
        return text_var

    def int_entry(self, label_text, default_int, row):
        text_var = tk.IntVar()
        tk.Label(self, text=label_text).grid(row=row, column=0, sticky='W')
        tk.Entry(self, textvariable=text_var).grid(row=row, column=1, sticky='W')
        text_var.set(default_int)
        return text_var

    def double_entry(self, label_text, default_double, row):
        text_var = tk.DoubleVar()
        tk.Label(self, text=label_text).grid(row=row, column=0, sticky='W')
        tk.Entry(self, textvariable=text_var).grid(row=row, column=1, sticky='W')
        text_var.set(default_double)
        return text_var

    def activate_button(self):
        print("Button clicked!")
        print(self.gather_settings())
        return self.gather_settings()

    def update_plot(self):
        plt.gcf().clear()
        self.s = np.random.random_sample(len(self.t))
        plt.plot(self.t, self.s)
        self.fig.canvas.draw()

    def plotter(self):
        plt.gcf().clear()
        self.s = np.random.random_sample(len(self.t))
        plt.plot(self.t, self.s)
        self.fig.canvas.draw()


if __name__ == '__main__':
    root = tk.Tk()
    app = Application(master=root)
    app.mainloop()
