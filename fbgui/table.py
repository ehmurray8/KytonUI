import tkinter.font as tkfont
import tkinter.ttk as ttk
import fbgui.ui_helper as uh
import tkinter as tk


class Table(ttk.Frame):
    """use a ttk.TreeView as a multicolumn ListBox"""

    def __init__(self, master=None, func=None):
        super().__init__(master)
        self.headers = []
        self.tree = None
        self.func = func
        self.item_ids = []

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

    def setup_headers(self, headers, reset=False):
        self.headers.clear()
        self.headers.extend(headers)
        if reset:
            if self.tree is not None:
                self.reset()
            self._setup_widgets()
        for i, col in enumerate(self.headers):
            self.tree.heading(col, text=col.title(), command=lambda c=col: uh.sort_column(self.tree, c, 0))
            # adjust the column's width to the header string
            self.tree.column(col, width=tkfont.Font().measure(col.title()))

    def add_data(self, item):
        new_item = []
        for i in item:
            if isinstance(i, float):
                new_item.append(round(i, 4))
            else:
                new_item.append(i)
        item = new_item
        self.item_ids.append(self.tree.insert('', 0, values=item))

        if len(uh.get_all_children_tree(self.tree)) > 100:
            try:
                self.tree.delete(self.item_ids.pop(0))
            except tk.TclError:
                pass

        # adjust column's width if necessary to fit each value
        for ix, val in enumerate(item):
            col_w = tkfont.Font().measure(val)
            if self.tree.column(self.headers[ix], width=None) < int(col_w * 2):
                self.tree.column(self.headers[ix], width=int(col_w * 2))

    def reset(self):
        self.item_ids.clear()
        self.tree.delete(*self.tree.get_children())
