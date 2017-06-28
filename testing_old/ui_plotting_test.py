import tkinter as tk

import matplotlib
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

matplotlib.use('TkAgg')


class PlotsFrame(tk.Frame):
    def __init__(self, master=None):
        super().__init__(master)
        self.grid()
        self.fig = plt.figure(1)
        plt.ion()
        self.t = np.arange(0.0, 3.0, 0.01)
        self.s = np.sin(np.pi * self.t)
        plt.plot(self.t, self.s)

        canvas = FigureCanvasTkAgg(self.fig, master=root)
        plot_widget = canvas.get_tk_widget()

        plot_widget.grid(row=0, column=0)
        tk.Button(root, text="Re-plot", command=self.plotter).grid(row=1, column=0)

    def plotter(self):
        plt.gcf().clear()
        self.s = np.random.random_sample(len(self.t))
        plt.plot(self.t, self.s)
        self.fig.canvas.draw()


if __name__ == "__main__":
    root = tk.Tk()
    app = PlotsFrame(master=root)
    app.mainloop()
