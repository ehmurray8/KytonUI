import tkinter as tk
import tkinter.font as tkFont
import tkinter.ttk as ttk


class McListBox(object):
    """use a ttk.TreeView as a multicolumn ListBox"""

    def __init__(self):
        self.tree = None
        self._setup_widgets()
        self._build_tree()

    def _setup_widgets(self):
        container = tk.Frame()
        container.grid()
        # text_var = tk.DoubleVar()

        containerb = tk.Frame()
        containerb.grid()
        ttk.Label(containerb, text="TESTING").pack()
        ttk.Entry(containerb, textvariable="TXT").pack()

        # create a treeview with dual scrollbars
        self.tree = ttk.Treeview(columns=data_header, show="headings")
        vsb = tk.Scrollbar(orient="vertical", command=self.tree.yview)
        hsb = tk.Scrollbar(orient="horizontal", command=self.tree.xview)
        self.tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)
        self.tree.grid(column=0, row=0, sticky='nsew', in_=container)
        vsb.grid(column=1, row=0, sticky='ns', in_=container)
        hsb.grid(column=0, row=1, sticky='ew', in_=container)
        container.grid_columnconfigure(0, weight=1)
        container.grid_rowconfigure(0, weight=1)

    def _build_tree(self):
        for col in data_header:
            self.tree.heading(col, text=col.title(), command=lambda c=col: sortby(self.tree, c, 0))
            # adjust the column's width to the header string
            self.tree.column(col, width=tkFont.Font().measure(col.title()))
        for item in data_list:
            self.tree.insert('', 'end', values=item)
            # adjust column's width if necessary to fit each value
            for ix, val in enumerate(item):
                col_w = tkFont.Font().measure(val)
                if self.tree.column(data_header[ix], width=None) < col_w:
                    self.tree.column(data_header[ix], width=col_w)


def sortby(tree, col, descending):
    """sort tree contents when a column header is clicked on"""
    # grab values to sort
    data = [(tree.set(child, col), child) for child in tree.get_children('')]
    # if the data to be sorted is numeric change to float
    # data =  change_numeric(data)
    # now sort the data in place
    data.sort(reverse=descending)
    for ix, item in enumerate(data):
        tree.move(item[1], '', ix)
    # switch the heading so it will sort in the opposite direction
    tree.heading(col, command=lambda col=col: sortby(tree, col, int(not descending)))


"""class Application(tk.Frame):
    def __init__(self, master=None):
        super().__init__(master)
        self.grid()

        # GRID LABELS

        # SAVE DATA BUTTONS
        self.save_sp_button = tk.Button(self, text="Save set-points", command=self.save_set_points)
        self.save_sp_button.grid(row=9, column=0)

        self.save_all_button = tk.Button(self, text="Save all points", command=self.save_set_points)
        self.save_all_button.grid(row=9, column=1)

    def save_set_points(self):
        print("Saving setpoints!")

    def save_all_points(self):
        print("Saving all points!")

    def update_table(self):
        print("Updating table!")"""


if __name__ == '__main__':
    # the test data ...

    data_header = ['Temperature', 'Wavelengths', 'Amplitudes', 'Setpoint', 'Serial number', 'Time seconds',
                   'Time milliseconds']
    data_list = [
        ('Hyundai', 'brakes', 'Persian', 'Malamute', 'E', 'F', 'G'),
        ('Honda', 'light', 'Forest cat', 'Dachshund', 'E', 'F', 'G'),
        ('Lexus', 'battery', 'ABC', 'ABC', 'E', 'F', 'G'),
        ('Benz', 'wiper', 'ABC', 'ABC', 'E', 'F', 'G'),
        ('Ford', 'tire', 'ABC', 'ABC', 'E', 'F', 'G'),
        ('Chevy', 'air', 'ABC', 'ABC', 'E', 'F', 'G'),
        ('Chrysler', 'piston', 'ABC', 'ABC', 'E', 'F', 'G'),
        ('Toyota', 'brake pedal', 'ABC', 'ABC', 'E', 'F', 'G'),
        ('BMW', 'seat', 'ABC', 'ABC', 'E', 'F', 'G'),
        ('HyundaiB', 'brakes', 'Persian', 'Malamute', 'E', 'F', 'G'),
        ('HondaB', 'light', 'Forest cat', 'Dachshund', 'E', 'F', 'G'),
        ('LexusB', 'battery', 'ABC', 'ABC', 'E', 'F', 'G'),
        ('BenzB', 'wiper', 'ABC', 'ABC', 'E', 'F', 'G'),
        ('FordB', 'tire', 'ABC', 'ABC', 'E', 'F', 'G'),
        ('ChevyB', 'air', 'ABC', 'ABC', 'E', 'F', 'G'),
        ('ChryslerB', 'piston', 'ABC', 'ABC', 'E', 'F', 'G'),
        ('ToyotaB', 'brake pedal', 'ABC', 'ABC', 'E', 'F', 'G'),
        ('BMWB', 'seat', 'ABC', 'ABC', 'E', 'F', 'G')
    ]
    root = tk.Tk()
    mc_listbox = McListBox()
    root.mainloop()
