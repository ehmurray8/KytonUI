import threading
import tkinter.font as tkFont
import tkinter.ttk as ttk
from dateutil import parser
import sqlite3
import fbgui.file_helper as fh
from fbgui.constants import CAL


class Table(ttk.Frame):
    """use a ttk.TreeView as a multicolumn ListBox"""

    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)
        self.headers = ["Id", "File name", "Program Type"]
        self.tree = None
        self.item_ids = []
        conn = sqlite3.connect("db/program_data.db")
        cur = conn.cursor()
        cur.execute("SELECT * FROM map;")
        res = cur.fetchall()
        ids = [tup[0] for tup in res]
        names = [tup[1] for tup in res]
        types = [tup[2] for tup in res]
        paths = [tup[3] for tup in res]
        snums = [tup[4] for tup in res]

        self.prog_info = {"Id": ids, "Name": names, "Type": types}
        self.file_paths = {i: path for i, path in zip(self.prog_info["Id"], paths)}
        self.snums = {i: snum for i, snum in zip(self.prog_info["Id"], snums)}
        conn.close()
        self._setup_widgets()
        self.setup_headers()
        for i, name, ptype in zip(self.prog_info["Id"][::-1], self.prog_info["Name"][::-1], self.prog_info["Type"][::-1]):
            self.add_data([i, name, ptype])

    def _setup_widgets(self):
        # create a treeview with dual scrollbars
        ttk.Label(self, text="Create Spreadsheet For a Recent Program").grid(sticky="nsew", pady=10)

        self.tree = ttk.Treeview(self, columns=self.headers, show="headings")
        vsb = ttk.Scrollbar(self, orient="vertical", command=self.tree.yview)
        hsb = ttk.Scrollbar(self, orient="horizontal", command=self.tree.xview)
        self.tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)
        self.tree.grid(column=0, row=1, sticky='nsew', in_=self)
        vsb.grid(column=1, row=1, sticky='ns', in_=self)
        hsb.grid(column=0, row=2, sticky='ew', in_=self)

        create_xcel = ttk.Button(self, text="Generate Spreadsheet for Selected", command=self.create_spreadsheet)
        create_xcel.grid(column=0, row=3, pady=10)
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

    def create_spreadsheet(self):
        for item in self.tree.selection():
            vals = self.tree.item(item)['values']
            fname = self.file_paths[vals[0]]
            snums = self.snums[vals[0]].split(",")
            threading.Thread(target=fh.create_excel_file, args=(fname, snums, vals[1] == CAL.lower())).start()

    def setup_headers(self):
        for i, col in enumerate(self.headers):
            self.tree.heading(col, text=col.title(), command=lambda c=col: sortby(self.tree, c, 0))
            # adjust the column's width to the header string
            self.tree.column(col, width=tkFont.Font().measure(col.title()))

    def get_all_children(self, item=""):
        children = self.tree.get_children(item)
        for child in children:
            children += self.get_all_children(child)
        return children

    def add_data(self, item):
        self.item_ids.append(self.tree.insert('', 'end', values=item))

        if len(self.get_all_children()) > 100:
            self.tree.delete(self.item_ids.pop(0))

        # adjust column's width if necessary to fit each value
        for ix, val in enumerate(item):
            col_w = tkFont.Font().measure(val)
            if self.tree.column(self.headers[ix], width=None) < int(col_w * 3):
                self.tree.column(self.headers[ix], width=int(col_w * 3))

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