<<<<<<< HEAD
#pylint:disable=unused-import
=======
#pylint:disable=unused-import, wrong-import-position
>>>>>>> 7071fa3c76f9efee35f4c1da8c2ba389da7b19e4
"""Main entry point for the UI."""
import tkinter as tk
import time
import sys

import matplotlib
<<<<<<< HEAD
import matplotlib.animation as animation
from matplotlib import style
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2TkAgg
from matplotlib.figure import Figure
import matplotlib.pyplot as plt
=======
matplotlib.use("TkAgg")
import matplotlib.animation as animation
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2TkAgg
from matplotlib.figure import Figure
from matplotlib import pyplot as plt
from matplotlib import style
>>>>>>> 7071fa3c76f9efee35f4c1da8c2ba389da7b19e4

#DEV_DISCONNECT
import controller_340_wrapper as temp_controller
import delta_oven_wrapper as oven_wrapper
import init_instruments as init
import sm125_wrapper
import create_options_panel as options_panel
import file_helper
<<<<<<< HEAD
#matplotlib.use("TkAgg")
style.use('ggplot')

=======

style.use("ggplot")

NUM_SNS = 4

>>>>>>> 7071fa3c76f9efee35f4c1da8c2ba389da7b19e4
class Application(tk.Frame): # pylint: disable=too-many-ancestors, too-many-instance-attributes
    """Class containing the main tkinter application."""
    def __init__(self, master):
        """Constructs the app."""
        super().__init__(master)

<<<<<<< HEAD
        #self.controller, self.oven, self.gp700, self.sm125 = init.setup_instruments()
=======
        if len(sys.argv) > 1 and sys.argv[1] == "-k":
            self.controller, self.oven, self.gp700, self.sm125 = init.setup_instruments()
>>>>>>> 7071fa3c76f9efee35f4c1da8c2ba389da7b19e4

        #Window setup
        master.title("Kyton Baking")
        self.menu = tk.Menu(master, tearoff=0)
        master.config(menu=self.menu)
        self.menu.add_command(label="Create Excel", command=self.create_excel)

        self.pack(side="top", fill="both", expand=True)
        self.main_frame = tk.Frame(self)
        self.options = options_panel.OptionsPanel(self.main_frame)
        self.options.create_start_btn(self.start)
        self.options.grid(row=0, column=0, sticky='ew')

        self.stable_count = 0

        self.main_frame.pack(expand=1, fill=tk.BOTH)

        self.x_vals = []
        self.y_vals = []
        self.num_pt = 0

        self.fig = plt.Figure()
        sub = self.fig.add_subplot(111)
        sub.set_title('Baking: ' + u'\u0394\u03BB' + " (pm) vs. Time (hr) from start")
        sub.set_ylabel(u'\u0394\u03BB' + " average (pm)")
        sub.set_xlabel('Elapsed Time from start (hr)')
        self.line = sub.plot(self.x_vals, self.y_vals)
        self.create_graph()


<<<<<<< HEAD
    def create_graph(self):
        """Creates the graph."""
        canvas = FigureCanvasTkAgg(self.fig, self.main_frame)
        canvas.show()
        canvas.get_tk_widget().grid(column=1, row=0)
        toolbar = NavigationToolbar2TkAgg(canvas, ROOT)
        toolbar.update()

        animation.FuncAnimation(self.fig, self.animate, frames=[self.num_pt]\
                , interval=5000, blit=False)
        plt.show()

    def animate(self, i):
        """Updates the graph."""
        print("Animate " + str(i) + " " + str(self.num_pt))
        self.x_vals.append(self.num_pt)
        self.y_vals.append(self.num_pt)
        self.num_pt += 1
        self.line.set_data(self.x_vals, self.y_vals)
        return self.line,
=======
    #def create_graph(self):
        #"""Creates the graph."""
        #canvas = FigureCanvasTkAgg(self.fig, self.main_frame)
        #canvas.show()
        #canvas.get_tk_widget().grid(column=1, row=0)
        #toolbar = NavigationToolbar2TkAgg(canvas, ROOT)
        #toolbar.update()

        #animation.FuncAnimation(self.fig, self.animate, frames=[self.num_pt]\
        #        , interval=5000, blit=False)
        #plt.show()

    #def animate(self, i):
    #    """Updates the graph."""
    #    print("Animate " + str(i) + " " + str(self.num_pt))
    #    self.x_vals.append(self.num_pt)
    #    self.y_vals.append(self.num_pt)
    #    self.num_pt += 1
    #    self.line.set_data(self.x_vals, self.y_vals)
    #    return self.line,
>>>>>>> 7071fa3c76f9efee35f4c1da8c2ba389da7b19e4

    def create_excel(self):
        """Creates excel file."""
        file_helper.create_excel_file(self.options.file_name.get())

    def start(self):
        """Starts the recording process."""
        if self.options.delta_oven_state.get():
<<<<<<< HEAD
            #DEV_DISCONNECT
            pass
            #oven_wrapper.set_temp(self.oven, self.options.baking_temp.get())
=======
            if len(sys.argv) > 1 and sys.argv[1] == "-k":
                oven_wrapper.set_temp(self.oven, self.options.baking_temp.get())
            else:
                pass
>>>>>>> 7071fa3c76f9efee35f4c1da8c2ba389da7b19e4
        self.program_loop()

    def check_stable(self):
        """Check if the program is ready to move to primary interval."""
        init_time = self.options.init_time.get()
        init_dur = self.options.init_duration.get() * 60
        num_stable = int(init_dur/init_time + .5)

        if self.stable_count < num_stable:
            self.stable_count += 1
            return False
        return True

    def program_loop(self):
        """Infinite program loop."""
        print("Started program loop...")
        if not self.check_stable():
            self.baking_loop()
            self.after(int(self.options.init_time.get()) * 1000, self.program_loop)
        else:
            self.baking_loop()
            self.after(int(self.options.prim_time.get()) * 1000 * 60, self.program_loop)

    def __avg_waves_amps(self):
        amplitudes_avg = []
        wavelengths_avg = []
        count = 0
        need_init = False
        while count < int(self.options.num_pts.get()):
<<<<<<< HEAD
            #DEV_DISCONNECT
            #wavelengths, amplitudes = sm125_wrapper.get_data_actual(self.sm125)

            #wavelengths, amplitudes = sm125_wrapper.get_data_channels(self.options.chan_nums)
            #TODO
            #Need to associate proper amplitudes/powers with correct serial number

            wavelengths = []
            amplitudes = []
=======
            if len(sys.argv) > 1 and sys.argv[1] == "-k":
                wavelengths, amplitudes = sm125_wrapper.get_data_actual(self.sm125)
            else:
                wavelengths = []
                amplitudes = []
>>>>>>> 7071fa3c76f9efee35f4c1da8c2ba389da7b19e4

            if not need_init:
                wavelengths_avg = [0] * len(wavelengths[0])
                amplitudes_avg = [0] * len(amplitudes[0])
                need_init = True

            i = 0
            for wavelength_list in wavelengths:
                for wavelength in wavelength_list:
                    wavelengths_avg[i] += wavelength
                    i += 1

            i = 0
            for ampl in amplitudes:
                for amp in ampl:
                    amplitudes_avg[i] += amp
                    i += 1

            count += 1

        i = 0
        while i < len(wavelengths_avg):
            wavelengths_avg[i] /= (count)
            amplitudes_avg[i] /= (count)
            i += 1
        return wavelengths_avg, amplitudes_avg


    def baking_loop(self):
        """Runs the baking process."""
        print("Started baking loop...")
<<<<<<< HEAD
        #DEV_DISCONNECT
        #temperature = temp_controller.get_temp_c(self.controller)
        #temperature = float(temperature[:-3])
        temperature = 0

        wavelengths_avg, amplitudes_avg = self.__avg_waves_amps()

        #DEV_DISCONNECT
        #temp2 = temp_controller.get_temp_c(self.controller)
        #temperature += float(temp2[:-3])
=======
        if len(sys.argv) > 1 and sys.argv[1] == "-k":
            temperature = temp_controller.get_temp_c(self.controller)
            temperature = float(temperature[:-3])
        else:
            temperature = 0

        wavelengths_avg, amplitudes_avg = self.__avg_waves_amps()

        if len(sys.argv) > 1 and sys.argv[1] == "-k":
            temp2 = temp_controller.get_temp_c(self.controller)
            temperature += float(temp2[:-3])
>>>>>>> 7071fa3c76f9efee35f4c1da8c2ba389da7b19e4
        temperature /= 2.0

        serial_nums = []
        for sn_ent in self.options.sn_ents:
            serial_nums.append(sn_ent.get())

        curr_time = time.time()
        file_helper.write_csv_file(self.options.file_name.get(), serial_nums, \
                    curr_time, temperature, wavelengths_avg, amplitudes_avg)

def start_bake():
    """Starts the baking program."""
    #pylint:disable=global-statement
    global INPT, NUM_SNS_ROOT, ROOT
    number = INPT.get()
    try:
        options_panel.NUM_SNS = int(number)
        NUM_SNS_ROOT.destroy()
        ROOT = tk.Tk()
        app = Application(master=ROOT)
        #open_center(750, 600, ROOT)
        app.mainloop()
    except ValueError:
        pass

def open_center(width, height, root):
    #pylint:disable=global-statement
    """Open num fiber dialog in center of the screen."""
    width_screen = root.winfo_screenwidth()
    height_screen = root.winfo_screenheight()

    x_cord = (width_screen/2) - (width/2)
    y_cord = (height_screen/2) - (height/2)

    root.geometry("{}x{}-{}+{}".format(int(width), int(height),\
                             int(x_cord), int(y_cord)))


if __name__ == "__main__":
    NUM_SNS_ROOT = tk.Tk()
    #NUM_SNS_ROOT.geometry("500x100-0+0")
    tk.Label(NUM_SNS_ROOT, text="How many fibers will be used for baking? ", \
            height=1, width=75).grid(row=0)
    INPT = tk.Entry(NUM_SNS_ROOT, width=25)
    INPT.grid(row=1, column=0)
    #INFO = tk.Label(NUM_SNS_ROOT, text="", height=1)
    #INFO.grid(row=3, column=1)
    START_BAKE = tk.Button(NUM_SNS_ROOT, text="Start Baking", command=start_bake)
    START_BAKE.grid(row=2, column=0)
    ROOT = None
    NUM_SNS_ROOT.title("Baking Settings")
    open_center(500, 100, NUM_SNS_ROOT)
    NUM_SNS_ROOT.mainloop()
