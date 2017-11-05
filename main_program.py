"""Module contains the main entry point for the Kyton UI."""

# pylint: disable=import-error, relative-import

import queue
import matplotlib
matplotlib.use("TkAgg")
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2TkAgg
from matplotlib.figure import Figure
import matplotlib.animation as animation
from matplotlib import style
from matplotlib.widgets import Button
from tkinter import messagebox
import tkinter as tk
from baking_program import BakingPage
from cal_program import CalPage
import ui_helper
import visa

LARGE_FONT = ("Verdana", 16)

OVEN = "Dicon Oven"
OVEN_LOC = 27

LASER = "Micron Optics SM125"
LASER_LOC = "10.0.0.122"
LASER_PORT = 50000

SWITCH = "Optical Switch"
SWITCH_LOC = "192.168.1.111"
SWITCH_PORT = 5000

TEMP = "LSC Temperature Controller"
TEMP_LOC = 12


class Application(tk.Tk):
    """Main Application class."""

    def __init__(self, *args, **kwargs):
        # pylint: disable=missing-super-argument
        super().__init__(*args, **kwargs)
        
        self.title("Kyton FBG UI")
        img = tk.PhotoImage(file=r'fiber.png')
        self.tk.call('wm', 'iconphoto', self._w, img)

        self.main_notebook = ttk.Notebook()
        self.enable_traversals()

        self.home_frame = ttk.Frame()
        self.main_notebook.add(self.home_frame, "Home")

        self.setup_home_frame()

        self.device_widgets = []
        self.main_queue = queue.Queue()
        self.manager = visa.ResourceManager()

        self.temp_controller = None
        self.oven = None
        self.laser = None
        self.switch = None

        self.cal_tabs = []
        self.bake_tabs = []

        # Store as instance variables so they do not get garbage collected.
        self.img_graph = tk.PhotoImage(file=r'graph.png')
        self.img_config = tk.PhotoImage(file=r'config.png')

    def setup_home_frame(self):
        device_frame = ttk.Frame(self.home_frame)

        ttk.Label(device_frame, text="Device").grid(0, column=0, sticky='ew')
        ttk.Label(device_frame, text="Location").grid(0, column=1, sticky='ew')
        ttk.Label(device_frame, text="Port").grid(0, column=2, sticky='ew')
        ttk.Button(device_frame, text="Connection Status").grid(0, column=3, sticky='ew')
        switch_conf = [(LASER, LASER_LOC, LASER_PORT), (SWITCH, SWITCH_LOC, SWITCH_PORT), 
                       (TEMP, TEMP_LOC, None), (OVEN, OVEN_LOC, None)]
        for i, dev in enumerate(switch_conf):
            self.device_entry(dev[0] dev[1], i+1, dev[2])
        self.device_frame.grid(sticky='ew')

        start_prog_frame = ttk.Frame(self.home_frame)
        ttk.Button(start_prog_frame, text="Start New Baking Run", command=self.create_bake_tab).pack()  
        ttk.Button(start_prog_frame, text="Start New Calibration Run", command=self.create_cal_tab).pack()
        
    def device_entry(self, dev_text, loc_str, row, port_str):
        """Creates an entry in the device grid for a device."""
        ttk.Entry(container, text=dev_text).grid(row=row, sticky='ew')

        loc_ent = ttk.Entry(container, text=loc_str)
        loc_ent.grid(row=row, column=1, sticky='ew')

        if port_str is not None:
            port_ent = ttk.Entry(container, text=port_str)
            port_ent.grid(row=row, sticky='ew', column=2)

        conn_butt = ttk.Button(container, text="Connect", command=self.conn_dev)
        conn_butt.grid(row=row, column=3, sticky='ew')
        
        self.device_widgets.append((loc_ent, port_ent, conn_butt))

    def conn_dev(self, loc_ent, port_ent, dev):
        if dev == TEMP:
            try:
                self.temp_controller = devices.TempController(int(loc_ent.get()), self.manager)
            except visa.VisaIOError:
                # Need to handle Connection Error
                pass
            except ValueError:
                # Need to handle invalid value
                pass
        elif dev == OVEN:
            try:
                self.oven = devices.Oven("GPIB0::{}::INSTR".format(int(loc_ent.get())), self.manager)
            except visa.VisaIOError:
                # Need to handle Connection Error
                pass
            except ValueError:
                # Need to handle invalid value
        elif dev == SWITCH:
            try:
                self.op_switch = devices.OpSwitch(loc_ent.get(), int(port_ent.get()))
            except socket.error:
                # Need to handle connection error
                pass
            except:
                # Need to handle invalid value
                pass
        elif dev == LASER:
            try:
                self.laser = devices.SM125(loc_ent.get(), int(port_ent.get()))
            except socket.error:
                # Need to handle connection error
                pass
            except ValueError:
                # Need to handle invalid value
                pass

    def create_bake_tab(self):
        # Need to add logic for confirming, and deleting any cal tabs
        bake_nb = ttk.Notebook()
        config_frame = ttk.Frame()
        graph_frame = ttk.Frame()
        self.bake_nb.add(config_frame, image=self.img_config)
        self.bake_nb.add(graph_frame, image=self.img_graph)
        self.bake_tabs.append(bake_nb)
        self.main_notebook.add(bake_nb, text="Bake {}".format(len(bake_tabs)))

        canvas = FigureCanvasTkAgg(fig, self.frame2)
        canvas.show()

        canvas_widget = canvas.get_tk_widget()
        canvas_widget.pack(side=tk.BOTTOM, fill=tk.BOTH, expand=True)


        self.cid = canvas.mpl_connect('button_press_event', self.onclick)

        self.toolbar = NavigationToolbar2TkAgg(canvas, self.frame2)
        self.toolbar.update()
        canvas._tkcanvas.pack(side=tk.TOP, fill=tk.BOTH, expand=True) 

    def create_cal_tab(self):
        # Need to add logic for confirming, and deleting any bake tabs

    def toggle_geom(self,event):
        geom=self.master.winfo_geometry()
        print(geom,self._geom)
        self.master.geometry(self._geom)
        self._geom=geom

    def graph_back(self, event, canvas, fig):
        if event.dblclick:
            self.ax_zoom.cla()
            fig.clf()
            canvas.draw()
            canvas.mpl_disconnect(self.cid)
            self.cid = canvas.mpl_connect('button_press_event', self.onclick)
            self.show_main_plots()
            canvas.draw()
            self.toolbar.update()

    def onclick(self, event, canvas, fig):
        for i, ax in enumerate(self.main_axes):
            if event.dblclick and ax == event.inaxes:
                #print("Click is in axes ax{}".format(i+1))
                for ax in self.main_axes:
                    ax.cla()
                fig.clf()
                canvas.draw()
                self.toolbar.update()

                self.ax_zoom = fig.add_subplot(111)
                canvas.mpl_disconnect(self.cid)
                self.cid = canvas.mpl_connect('button_press_event', self.graph_back)

                self.ax_zoom.plot(np.random.rand(10))
                canvas.draw()
                break

    def show_main_plots(self, fig):
        self.axis1 = fig.add_subplot(231)
        self.axis1.plot(np.random.rand(10))
        self.axis2 = fig.add_subplot(232)
        self.axis2.plot(np.random.rand(10))
        self.axis3 = fig.add_subplot(233)
        self.axis3.plot(np.random.rand(10))
        self.axis4 = fig.add_subplot(234)
        self.axis4.plot(np.random.rand(10))
        self.axis5 = fig.add_subplot(235)
        self.axis5.plot(np.random.rand(10))
        self.axis6 = fig.add_subplot(236)
        self.axis6.plot(np.random.rand(10))
        self.main_axes = [self.axis1, self.axis2, self.axis3, self.axis4, self.axis5, self.axis6]


    def tkloop(self):
        """Loop for threaded processes."""
        try:
            while True:
                func, args, kwargs = self.main_queue.get_nowait()
                func(*args, **kwargs)
        except queue.Empty:
            pass

        self.after(200, self.tkloop)

if __name__ == "__main__":
    APP = Application()
    APP.tkloop()
    APP.mainloop()
