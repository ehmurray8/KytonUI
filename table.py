import tkinter.font as tkFont
import tkinter.ttk as ttk
from dateutil import parser

class Table(ttk.Frame):
    """use a ttk.TreeView as a multicolumn ListBox"""

    def __init__(self, master=None, func=None):
        super().__init__(master)
        self.headers = []
        self.tree = None
        self.func = func

    def _setup_widgets(self):
        # create a treeview with dual scrollbars
        self.tree = ttk.Treeview(self, columns=self.headers, show="headings")
        vsb = ttk.Scrollbar(self, orient="vertical", command=self.tree.yview)
        hsb = ttk.Scrollbar(self, orient="horizontal", command=self.tree.xview)
        self.tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)
        self.tree.grid(column=0, row=0, sticky='nsew', in_=self)
        vsb.grid(column=1, row=0, sticky='ns', in_=self)
        hsb.grid(column=0, row=1, sticky='ew', in_=self)
        create_xcel = ttk.Button(self, text="Create Excel Spreadsheet", command=self.func)
        create_xcel.grid(column=0, row=2)
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)

    def setup_headers(self, headers):
        self.headers.extend(headers)
        self._setup_widgets()
        for i, col in enumerate(self.headers):
            self.tree.heading(col, text=col.title(), command=lambda c=col: sortby(self.tree, c, 0))
            # adjust the column's width to the header string
            self.tree.column(col, width=tkFont.Font().measure(col.title()))

    def add_data(self, item):
        self.tree.insert('', 'end', values=item)
        # adjust column's width if necessary to fit each value
        for ix, val in enumerate(item):
            col_w = tkFont.Font().measure(val)
            if self.tree.column(self.headers[ix],width=None)<int(col_w * 1.6):
                self.tree.column(self.headers[ix], width=int(col_w * 1.6))

    def reset(self):
        self.tree.delete(*self.tree.get_children())

def sortby(tree, col, descending):
    """sort tree contents when a column header is clicked on"""
    # grab values to sort
    data = [(tree.set(child, col), child) for child in tree.get_children('')]
    # if the data to be sorted is numeric change to float
    try_date = False
    try:
        data = [(float(d[0]), d[1]) for d in data]
    except ValueError:
        try_date = True

    if try_date:
        try:
            data = [(parser.parse(d[0]), d[1]) for d in data]
        except ValueError:
            pass

    # now sort the data in place
    data.sort(reverse=descending)
    for ix, item in enumerate(data):
        tree.move(item[1], '', ix)
    # switch the heading so it will sort in the opposite direction
    tree.heading(col, command=lambda col=col: sortby(tree, col, int(not descending)))