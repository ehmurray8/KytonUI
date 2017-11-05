from tkinter import ttk
import tkinter as tk
import matplotlib
matplotlib.use("TkAgg")
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2TkAgg
from matplotlib.figure import Figure
import matplotlib.animation as animation
from matplotlib import style
from matplotlib.widgets import Button
import numpy as np
style.use('ggplot')

pad = 3

class Test(tk.Tk):
    def __init__(self, *args, **kwargs):
        self.fig = Figure(figsize=(5,5), dpi=100)
        self.show_main_plots()
        super().__init__(*args, **kwargs)

        white = "#f0eff4"
        az_white = "#dcedff"
        lcbl_blue = "#94b0da"
        onyx = "#343f3e"
        nickel = "#727d71"

        med_blue = "#0B3C5D"
        sky_blue = "#328CC1"
        gold = "#D9B310"
        black = "#1D2731"

        bg_color = black
        tab_color = sky_blue
        tabs_color = az_white

        style = ttk.Style()
        style.theme_create("outer", parent="alt", settings={
            ".": {"configure": {"background": bg_color}},
            "TFrame": {"configure": {"background": bg_color}},
            "TNotebook": {"configure": {"tabmargins": [10, 10, 10, 2]}},
            "TNotebook.Tab": {
                "configure": {"padding": [10, 4], "font": ('Helvetica', 18), "background": tab_color},
                "map":       {"background": [("selected", tabs_color)], "font": [("selected", ('Helvetica', 18, "bold"))],
                              "expand": [("selected", [1, 1, 1, 0])]}}})

        style.theme_use("outer")
        self.notebook = ttk.Notebook(style='OuterNB.TNotebook')
        self.notebook.enable_traversal()
        s = ttk.Style()
        s.configure('InnerNB.TNotebook', tabposition='wn')
        self.notebook_inner = ttk.Notebook(style='InnerNB.TNotebook')
        self.frame = ttk.Frame()
        self.tmp_lbl1 = tk.Label(self.frame, text="I'm in Frame 1!")
        self.tmp_lbl1.pack(side="top", expand=True, padx=10, pady=5)
        b = tk.Button(self.frame, text="Add New", command=self.add_new)
        b.pack()
        tk.Button(self.frame, text="Add New Tab", command=self.add_main_tab).pack()
        tk.Button(self.frame, text="Remove Tab", command=self.rm_tab).pack()

        frame1 = ttk.Frame()
        tk.Label(frame1, text="I'm in Frame Outer!").\
            pack(side="top", expand=True, padx=10, pady=5)

        #Graphing Frame
        self.frame2 = ttk.Frame()
        
        self.img_graph = tk.PhotoImage(file=r'graph.png')
        self.img_setts = tk.PhotoImage(file=r'config.png')
        self.notebook_inner.add(self.frame, image=self.img_setts)  # , text="Frame")
        self.notebook_inner.add(self.frame2, image=self.img_graph)
        
        self.notebook.add(self.notebook_inner, text='Test')
        self.notebook.add(frame1, text="Frame Outer")
        self.notebook.pack(side="top", fill="both", expand=True)


        self.canvas = FigureCanvasTkAgg(self.fig, self.frame2)
        self.canvas.show()

        self.canvas_widget = self.canvas.get_tk_widget()
        self.canvas_widget.pack(side=tk.BOTTOM, fill=tk.BOTH, expand=True)


        self.cid = self.canvas.mpl_connect('button_press_event', self.onclick)

        self.toolbar = NavigationToolbar2TkAgg(self.canvas, self.frame2)
        self.toolbar.update()
        self.canvas._tkcanvas.pack(side=tk.TOP, fill=tk.BOTH, expand=True) 

        self.back_button = ttk.Button(self.frame2, text="Back", command=self.graph_back)
        self.back_button.pack(side = tk.RIGHT)


        self.geometry("{0}x{1}+0+0".format(
            self.winfo_screenwidth()-pad, self.winfo_screenheight()-pad))
        self.bind('<Escape>',self.toggle_geom)            

        self.ax_zoom = None
        self.back_button = None
        self.tmp_frame = None

    def add_new(self):
        b = tk.Button(self.frame,text="Click to destroy")
        b.pack()
        b.config(command=b.pack_forget) 

    def rm_tab(self):
        if self.tmp_frame is not None:
            self.notebook.forget(self.tmp_frame)
            self.tmp_frame = None

    def add_main_tab(self):
        if self.tmp_frame is None:
            self.tmp_frame = ttk.Frame()
            self.notebook.add(self.tmp_frame, text="New Tab")
        
    def toggle_geom(self,event):
        geom=self.master.winfo_geometry()
        print(geom,self._geom)
        self.master.geometry(self._geom)
        self._geom=geom

    def graph_back(self, event):
        if event.dblclick:
            self.ax_zoom.cla()
            self.fig.clf()
            self.canvas.draw()
            self.canvas.mpl_disconnect(self.cid)
            self.cid = self.canvas.mpl_connect('button_press_event', self.onclick)
            self.show_main_plots()
            self.canvas.draw()
            self.toolbar.update()


    def onclick(self, event):
        for i, ax in enumerate(self.main_axes):
            # For infomation, print which axes the click was in
            if event.dblclick and ax == event.inaxes:
                print("Click is in axes ax{}".format(i+1))
                for ax in self.main_axes:
                    ax.cla()
                self.fig.clf()
                self.canvas.draw()
                self.toolbar.update()

                self.ax_zoom = self.fig.add_subplot(111)
                self.canvas.mpl_disconnect(self.cid)
                self.cid = self.canvas.mpl_connect('button_press_event', self.graph_back)

                self.ax_zoom.plot(np.random.rand(10))
                self.canvas.draw()
                break


    def show_main_plots(self):
        self.axis1 = self.fig.add_subplot(231)
        self.axis1.plot(np.random.rand(10))
        self.axis2 = self.fig.add_subplot(232)
        self.axis2.plot(np.random.rand(10))
        self.axis3 = self.fig.add_subplot(233)
        self.axis3.plot(np.random.rand(10))
        self.axis4 = self.fig.add_subplot(234)
        self.axis4.plot(np.random.rand(10))
        self.axis5 = self.fig.add_subplot(235)
        self.axis5.plot(np.random.rand(10))
        self.axis6 = self.fig.add_subplot(236)
        self.axis6.plot(np.random.rand(10))
        self.main_axes = [self.axis1, self.axis2, self.axis3, self.axis4, self.axis5, self.axis6]

if __name__ == "__main__":
    TEST = Test()
    TEST.mainloop()
