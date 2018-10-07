"""Home page table used for creating excel spreadsheets of program runs."""
from queue import Queue
from typing import List, Dict
import threading
import tkinter
import tkinter.font as tkfont
import tkinter.ttk as ttk
from tkinter import LEFT, E, RIGHT, W
import sqlite3
from fbgui.excel_file_controller import ExcelFileController
from fbgui.constants import CAL, DB_PATH
from fbgui import ui_helper as uh
from fbgui.messages import MessageType, Message


class ExcelTable(ttk.Frame):
    """
    Tkinter frame containing widgets for creating excel spreadsheets.

    :ivar List[str] headers: the treeview table headers
    :ivar Queue main_queue: main_queue parameter
    :ivar ttk.Treeview tree: ttk tree displaying information about the program runs
    :ivar List[int] item_ids: ids of the items currently stored in the tree
    :ivar Dict[int: str] file_paths: mapping of map table ids to file paths
    :ivar List[str] s_nums: map of program database ids to comma separated strings of serial numbers for that program
    """

    def __init__(self, master: ttk.Frame, main_queue: Queue, **kwargs):
        """
        Create the widgets, populate the table, and pack into the master frame.

        :param master: parent frame for this class
        :param main_queue: queue used for writing log messages
        :param kwargs: additional parameters to pass to the ttk Frame super constructor
        """
        super().__init__(master, **kwargs)
        self.headers = ["Id", "File name", "Program Type"]
        self.main_queue = main_queue
        self.tree = None  # type: ttk.Treeview
        self.item_ids = []  # type: List[int]
        self.file_paths = None  # type: Dict[int, str]
        self.s_nums = None  # type: List[str]
        self._setup_widgets()
        self._setup_headers()
        self.refresh()

    def refresh(self):
        """Refreshes the table and loads all of the programs from the map database table."""
        for child in uh.get_all_children_tree(self.tree):
            self.tree.delete(child)
        self.item_ids.clear()
        conn = sqlite3.connect(DB_PATH)
        cur = conn.cursor()
        cur.execute("SELECT * FROM map;")
        res = cur.fetchall()
        ids = [tup[0] for tup in res]
        names = [tup[1] for tup in res]
        types = [tup[2] for tup in res]
        paths = [tup[3] for tup in res]
        snums = [tup[4] for tup in res]

        prog_info = {"Id": ids, "Name": names, "Type": types}
        self.file_paths = {i: path for i, path in zip(prog_info["Id"], paths)}
        self.s_nums = {i: snum for i, snum in zip(prog_info["Id"], snums)}
        conn.close()
        for i, name, ptype in zip(prog_info["Id"][::-1], prog_info["Name"][::-1], prog_info["Type"][::-1]):
            self.add_data([i, name, ptype])

    def _setup_widgets(self):
        """Initializes the widgets for this frame."""
        top_frame = ttk.Frame(self)
        top_frame.grid(sticky="nsew", pady=10)
        ttk.Label(top_frame, text="Create Spreadsheet For a Recent Program").pack(side=LEFT, anchor=W)
        ttk.Button(top_frame, command=self.refresh, text="Refresh").pack(side=RIGHT, anchor=E)

        self.tree = ttk.Treeview(self, columns=self.headers, show="headings")
        vsb = ttk.Scrollbar(self, orient="vertical", command=self.tree.yview)
        hsb = ttk.Scrollbar(self, orient="horizontal", command=self.tree.xview)
        self.tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)
        self.tree.grid(column=0, row=1, sticky='nsew', in_=self)
        vsb.grid(column=1, row=1, sticky='ns', in_=self)
        hsb.grid(column=0, row=2, sticky='ew', in_=self)

        create_excel = ttk.Button(self, text="Generate Spreadsheet for Selected", command=self.create_spreadsheet)
        create_excel.grid(column=0, row=3, pady=10)
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

    def create_spreadsheet(self):
        """Create the spreadsheet(s) for the selected elements of the tree view."""
        for item in self.tree.selection():
            values = self.tree.item(item)['values']
            f_name = self.file_paths[values[0]]
            s_nums = self.s_nums[values[0]].split(",")
            threading.Thread(target=self.show_spreadsheet, args=(f_name, s_nums, values[2])).start()

    def show_spreadsheet(self, file_path: str, fbg_names: List[str], program_type: str):
        excel_controller = ExcelFileController(file_path, fbg_names, self.main_queue, program_type.capitalize())
        excel_controller.create_excel()

    def _setup_headers(self):
        """Sets up the tree view headers."""
        for i, col in enumerate(self.headers):
            self.tree.heading(col, text=col.title(), command=lambda c=col: uh.sort_column(self.tree, c, False))
            self.tree.column(col, width=tkfont.Font().measure(col.title()))

    def add_data(self, item: List[str]):
        """
        Adds data to the tree view for a program stored in the map database table.

        :param item: list of strings for the program id, program name, and program type respectively
        """
        self.item_ids.append(self.tree.insert('', 'end', values=item))

        if len(uh.get_all_children_tree(self.tree)) > 100:
            try:
                self.tree.delete(self.item_ids.pop(0))
            except tkinter.TclError:
                self.master.main_queue.put(Message(MessageType.DEVELOPER, "Tree Deletion Error",
                                                   "Failed to delete item from the create excel view."))

        for ix, val in enumerate(item):
            col_w = tkfont.Font().measure(val)
            if self.tree.column(self.headers[ix], width=None) < int(col_w):
                self.tree.column(self.headers[ix], width=int(col_w))