"""Tkinter frame for the data view in the program."""
import tkinter as tk
import tkinter.font as tkfont
import tkinter.ttk as ttk
from queue import Queue
from typing import List, Callable

import fbgui.ui_helper as uh
from fbgui.messages import MessageType, Message


class DataTable(ttk.Frame):
    """
    Overrides ttk Frame class used to create a data view.

    :ivar List[str] headers: headers for the tree view widget
    :ivar ttk.Treeview tree: tree used for displaying the data
    :ivar Callable func: param func
    :ivar List[int] item_ids: ids of the items currently stored in the tree view
    :ivar Queue main_queue: param main_queue
    """

    def __init__(self, master: ttk.Frame, create_excel_func: Callable, main_queue: Queue=None):
        """
        Creates the data table frame.

        :param master: ttk frame that will be the parent of this object
        :param create_excel_func: program identifier string
        :param main_queue: if present, used for writing messages to the log view
        """
        super().__init__(master)
        self.headers = []
        self.tree = None
        self.create_excel_func = create_excel_func
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

        create_xcel = ttk.Button(self, text="Create Excel Spreadsheet", command=self.create_excel_func)
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
        for i, column in enumerate(self.headers):
            self.tree.heading(column, text=column.title(), command=lambda c=column: uh.sort_column(self.tree, c, False))
            column_width = tkfont.Font().measure(column.title())
            self.tree.column(self.headers[i], width=int(column_width * 1.2))

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
            except tk.TclError:
                self.master.main_queue.put(Message(MessageType.DEVELOPER, "Tree Deletion Error",
                                                   "Failed to delete item from the table view."))

        for i, val in enumerate(item):
            try:
                self.tree.column(self.headers[i])
            except IndexError:
                pass

    def reset(self):
        """Clears the tree view."""
        self.item_ids.clear()
        self.tree.delete(*self.tree.get_children())
