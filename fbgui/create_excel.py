import threading
import tkinter.font as tkfont
import tkinter.ttk as ttk
from tkinter import LEFT, E
import tkinter
import sqlite3
from fbgui import file_helper as fh
from fbgui.constants import CAL, DB_PATH
from fbgui import ui_helper as uh


class Table(ttk.Frame):
    """use a ttk.TreeView as a multicolumn ListBox"""

    def __init__(self, master: ttk.Frame, **kwargs):
        super().__init__(master, **kwargs)
        self.headers = ["Id", "File name", "Program Type"]
        self.tree = None
        self.item_ids = []
        self.prog_info = None
        self.file_paths = None
        self.snums = None
        self._setup_widgets()
        self.setup_headers()
        self.refresh()

    def refresh(self):
        for child in uh.get_all_children_tree(self.tree):
            self.tree.delete(child)
        conn = sqlite3.connect(DB_PATH)
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
        for i, name, ptype in zip(self.prog_info["Id"][::-1], self.prog_info["Name"][::-1],
                                  self.prog_info["Type"][::-1]):
            self.add_data([i, name, ptype])

    def _setup_widgets(self):
        # create a treeview with dual scrollbars
        top_frame = ttk.Frame(self)
        top_frame.grid(sticky="nsew", pady=10)
        ttk.Label(top_frame, text="Create Spreadsheet For a Recent Program").pack(side=LEFT, anchor='w')
        ttk.Button(top_frame, command=self.refresh, text="Refresh").pack(side=LEFT, anchor=E, padx=120)

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
            threading.Thread(target=fh.create_excel_file, args=(fname, snums, vals[2] == CAL.lower())).start()

    def setup_headers(self):
        for i, col in enumerate(self.headers):
            self.tree.heading(col, text=col.title(), command=lambda c=col: uh.sort_column(self.tree, c, 0))
            # adjust the column's width to the header string
            self.tree.column(col, width=tkfont.Font().measure(col.title()))

    def add_data(self, item):
        self.item_ids.append(self.tree.insert('', 'end', values=item))

        if len(uh.get_all_children_tree(self.tree)) > 100:
            try:
                self.tree.delete(self.item_ids.pop(0))
            except tkinter.TclError:
                pass

        # adjust column's width if necessary to fit each value
        for ix, val in enumerate(item):
            col_w = tkfont.Font().measure(val)
            if self.tree.column(self.headers[ix], width=None) < int(col_w * 3):
                self.tree.column(self.headers[ix], width=int(col_w * 3))
