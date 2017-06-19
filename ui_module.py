import tkinter as tk
import tkinter.font as tkfont
import tkinter.ttk as ttk
import config
import matplotlib
matplotlib.use('TkAgg')
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import matplotlib.pyplot as plt
import main_run

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
        plt.plot(config.x, config.y)

        canvas = FigureCanvasTkAgg(self.fig, master=config.root)
        plot_widget = canvas.get_tk_widget()

        plot_widget.grid(row=0, column=1)
        tk.Button(config.root, text="Re-plot", command=self.update_plot).grid(row=1, column=1)

        # TABLE
        self.tree = None
        self._setup_table()
        self._build_tree()

    def gather_settings(self):
        return self.controller_text.get(), \
               self.oven_text.get(), \
               self.interrogator_ip_text.get(), \
               self.interrogator_port_text.get(),\
               self.drift_number_text.get(),\
               self.wait_time_text.get(),\
               eval(self.set_point_list_text.get()),\
               self.dwell_text.get(),\
               eval(self.ranges_text.get())

    def string_entry(self, label_text, default_str, row):
        text_var = tk.StringVar()
        tk.Label(self, text=label_text).grid(row=row, column=0, sticky='ew')
        tk.Entry(self, textvariable=text_var).grid(row=row, column=1, sticky='ew')
        text_var.set(default_str)
        return text_var

    def int_entry(self, label_text, default_int, row):
        text_var = tk.IntVar()
        tk.Label(self, text=label_text).grid(row=row, column=0, sticky='ew')
        tk.Entry(self, textvariable=text_var).grid(row=row, column=1, sticky='ew')
        text_var.set(default_int)
        return text_var

    def double_entry(self, label_text, default_double, row):
        text_var = tk.DoubleVar()
        tk.Label(self, text=label_text).grid(row=row, column=0, sticky='ew')
        tk.Entry(self, textvariable=text_var).grid(row=row, column=1, sticky='ew')
        text_var.set(default_double)
        return text_var

    def activate_button(self):
        print(self.gather_settings())
        controller_, oven_, interrogator_socket_, ip_, num_temps_for_drift_, wait_time_between_points_, \
        list_of_sp_, temperature_ranges_, dwell_time_value_ = self.gather_settings()
        main_run.main_control(self, controller_, oven_, interrogator_socket_, num_temps_for_drift_, wait_time_between_points_,
                              list_of_sp_, temperature_ranges_, dwell_time_value_)
        return self.gather_settings()

    def update_plot(self):#, x, y):
        self._build_tree()
        plt.gcf().clear()
        #plt.plot(x, y)
        #self.fig.canvas.draw()

    def _setup_table(self):
        container = ttk.Frame()
        container.grid(column=2, row=0, sticky='nsew')
        # create a treeview with dual scrollbars
        self.tree = ttk.Treeview(columns=config.data_header, show="headings")
        vsb = ttk.Scrollbar(orient="vertical", command=self.tree.yview)
        hsb = ttk.Scrollbar(orient="horizontal", command=self.tree.xview)
        self.tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)
        self.tree.grid(column=2, row=0, sticky='nsew', in_=container)
        vsb.grid(column=3, row=0, sticky='ns', in_=container)
        hsb.grid(column=2, row=1, sticky='ew', in_=container)
        container.grid_columnconfigure(2, weight=1)
        container.grid_rowconfigure(2, weight=1)

    def _build_tree(self):
        for col in config.data_header:
            self.tree.heading(col, text=col.title(), command=lambda c=col: sortby(self.tree, c, 0))
            # adjust the column's width to the header string
            self.tree.column(col, width=tkfont.Font().measure(col.title()))
        for item in config.set_points_only_data:
            self.tree.insert('', 'end', values=item)
            # adjust column's width if necessary to fit each value
            for ix, val in enumerate(item):
                col_w = tkfont.Font().measure(val)
                if self.tree.column(config.data_header[ix], width=None) < col_w:
                    self.tree.column(config.data_header[ix], width=col_w)


def sortby(tree, _col, descending):
    """sort tree contents when a column header is clicked on"""
    # grab values to sort
    data = [(tree.set(child, _col), child) for child in tree.get_children('')]
    # if the data to be sorted is numeric change to float
    # data =  change_numeric(data)
    # now sort the data in place
    data.sort(reverse=descending)
    for ix, item in enumerate(data):
        tree.move(item[1], '', ix)
    # switch the heading so it will sort in the opposite direction
    tree.heading(_col, command=lambda col=_col: sortby(tree, _col, int(not descending)))
