#pylint:disable=unused-import
"""Main entry point for the UI."""
import tkinter as tk
import time

#import matplotlib
#import matplotlib.animation as animation
#from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2TkAgg
#from matplotlib.figure import Figure
#from matplotlib import pyplot as plt

#DEV_DISCONNECT
import controller_340_wrapper as temp_controller
import delta_oven_wrapper as oven_wrapper
import init_instruments as init
import sm125_wrapper
import create_options_panel as options_panel
import file_helper
#matplotlib.use("TkAgg")

NUM_SNS = 4

class Application(tk.Frame): # pylint: disable=too-many-ancestors
    """Class containing the main tkinter application."""
    def __init__(self, master):
        """Constructs the app."""
        super().__init__(master)

        #self.controller, self.oven, self.gp700, self.sm125 = init.setup_instruments()

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

        #self.x_vals = []
        #self.y_vals = []
        #self.num_pt = 0

        #self.fig = plt.Figure()
        #sub = self.fig.add_subplot(111)
        #sub.set_title('Baking: ' + u'\u0394\u03BB' + " (pm) vs. Time (hr) from start")
        #sub.set_ylabel(u'\u0394\u03BB' + " average (pm)")
        #sub.set_xlabel('Elapsed Time from start (hr)')
        #self.line = sub.plot(self.x_vals, self.y_vals)
        #self.create_graph()


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

    def create_excel(self):
        """Creates excel file."""
        file_helper.create_excel_file(self.options.file_name.get())

    def start(self):
        """Starts the recording process."""
        if self.options.delta_oven_state.get():
            #DEV_DISCONNECT
            pass
            #oven_wrapper.set_temp(self.oven, self.options.baking_temp.get())
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
            #DEV_DISCONNECT
            #wavelengths, amplitudes = sm125_wrapper.get_data_actual(self.sm125)
            wavelengths = []
            amplitudes = []

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
        #DEV_DISCONNECT
        #temperature = temp_controller.get_temp_c(self.controller)
        #temperature = float(temperature[:-3])
        temperature = 0

        wavelengths_avg, amplitudes_avg = self.__avg_waves_amps()

        #DEV_DISCONNECT
        #temp2 = temp_controller.get_temp_c(self.controller)
        #temperature += float(temp2[:-3])
        temperature /= 2.0

        serial_nums = []
        for sn_ent in self.options.sn_ents:
            serial_nums.append(sn_ent.get())

        curr_time = time.time()
        file_helper.write_csv_file(self.options.file_name.get(), serial_nums, \
                    curr_time, temperature, wavelengths_avg, amplitudes_avg)

if __name__ == "__main__":
    ROOT = tk.Tk()
    APP = Application(master=ROOT)
    APP.mainloop()
