"""Tkinter frame for the data view in the program."""
from queue import Queue
from typing import List
import tkinter.font as tkfont
import tkinter.ttk as ttk
import tkinter as tk
import fbgui.ui_helper as uh
from fbgui.messages import MessageType, Message


class DataTable(ttk.Frame):
    """Overrides ttk Frame class used to create a data view."""

    def __init__(self, master: ttk.Frame=None, func: str=None, main_queue: Queue=None):
        """
        Creates the data table frame.

        :param master: ttk frame that will be the parent of this object
        :param func: program identifier string
        :param main_queue: if present, used for writing messages to the log view

        :ivar headers: headers for the tree view widget
        :ivar tree: tree used for displaying the data
        :ivar func: param func
        :ivar item_ids: ids of the items currently stored in the tree view
        :ivar main_queue: param main_queue
        """
        super().__init__(master)
        self.headers = []
        self.tree = None
        self.func = func
        self.item_ids = []
        self.main_queue = main_queue

    def _setup_widgets(self):
        """Creates the widgets that will be in the frame."""
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

    def setup_headers(self, headers: List[str], reset: bool=False):
        """
        Sets up the headers for the tree view.

        :param headers: list of header strings to add to the tree view
        :param reset: If true clear the table
        """
        self.headers.clear()
        self.headers.extend(headers)
        if reset:
            if self.tree is not None:
                self.reset()
            self._setup_widgets()
        for i, col in enumerate(self.headers):
            self.tree.heading(col, text=col.title(), command=lambda c=col: uh.sort_column(self.tree, c, 0))
            self.tree.column(col, width=tkfont.Font().measure(col.title()))

    def add_data(self, item: List[str]):
        """
        Adds the values in item as a row in the tree view.

        :param item: list of strings corresponding to the columns in the tree view
        """
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
            except tk.TclError as t:
                self.master.main_queue.put(Message(MessageType.DEVELOPER, "Tree Deletion Error",
                                                   "Failed to delete item from the table view."))

        for ix, val in enumerate(item):
            col_w = tkfont.Font().measure(val)
            if self.tree.column(self.headers[ix], width=None) < int(col_w * 2):
                self.tree.column(self.headers[ix], width=int(col_w * 2))

    def reset(self):
        """Clears the tree view."""
        self.item_ids.clear()
        self.tree.delete(*self.tree.get_children())
