import configparser
import os
import tkinter as tk
from typing import List
from tkinter import ttk, filedialog, messagebox as mbox
from dateutil import parser
from constants import ENTRY_FONT, ARRAY_ENTRY_COLOR, DOCS_ICON, PROG_CONFIG_PATH
from PIL import ImageTk
import constants
import functools


def ui_entry(var_type, use_func=False):
    def _ui_entry(func):
        @functools.wraps(func)
        def _wrapper(container, label_text, row, width, default=None):
            var = var_type()
            ttk.Label(container, text=label_text).grid(row=row, column=0, sticky='ew')
            ttk.Entry(container, textvariable=var, width=width, font=ENTRY_FONT)\
                .grid(row=row, column=2, columnspan=2, sticky='ew')
            if default:
                var.set(default)
            if use_func:
                func(var, container, row)
            return var
        return _wrapper
    return _ui_entry


@ui_entry(tk.StringVar, True)
def file_entry(text_var: tk.StringVar, container: ttk.Frame, row: int):
    """Creates an entry with a browse button for the excel file."""
    docs_photo = ImageTk.PhotoImage(DOCS_ICON)
    browse_button = ttk.Button(container, image=docs_photo, command=lambda: browse_file(text_var), width=10)
    browse_button.grid(column=4, row=row, sticky=(tk.E, tk.W), padx=5, pady=5)
    browse_button.image = docs_photo


@ui_entry(tk.IntVar)
def int_entry(): pass


@ui_entry(tk.DoubleVar)
def double_entry(): pass


def checkbox_entry(container, label_text, row, checked=True):
    """Creates a checkbox entry, and returns a reference to the entry var."""
    int_var = tk.IntVar()
    ttk.Label(container, text=label_text).grid(row=row, column=0, sticky='ew')
    checkbox = ttk.Checkbutton(container, variable=int_var, width=5)
    checkbox.grid(row=row, column=2, sticky='ew')
    if checked:
        checkbox.invoke()
    return int_var


def array_entry(container, label_text, row, width, height, default_arr=None):
    """Creates an entry to import multiline text."""
    ttk.Label(container, text=label_text).grid(row=row, column=0, sticky='ew')
    text = tk.Text(container, width=width, height=height, bg=ARRAY_ENTRY_COLOR, font=ENTRY_FONT)
    text.grid(row=row, column=2, sticky='ew', columnspan=2)

    text.delete(1.0, tk.END)
    if default_arr is not None:
        text.insert(1.0, str(default_arr))
    return text


def device_entry(container: ttk.Frame, dev_text: str, loc_str: str, row: int, port_str: str,
                 loc_var: tk.StringVar, port_var: tk.StringVar):
    """Creates an entry in the device grid for a device."""
    dev_widg = ttk.Label(container, text=dev_text)
    dev_widg.grid(row=row, column=1, sticky='nsew')

    loc_ent = ttk.Entry(container, font=ENTRY_FONT, textvariable=loc_var)
    loc_ent.delete(0, tk.END)
    loc_ent.insert(tk.INSERT, loc_str)
    loc_ent.grid(row=row, column=3, sticky='ew')

    if port_str is not None:
        port_ent = ttk.Entry(container, font=ENTRY_FONT, textvariable=port_var)
        port_ent.delete(0, tk.END)
        port_ent.insert(tk.INSERT, port_str)
        port_ent.grid(row=row, sticky='ew', column=5)


def units_entry(container, label_text, row, width, unit, default_double=0.0):
    """Creates a time entry, and returns a reference to the entry var."""
    text_var = double_entry(container, label_text, row, width, default_double)
    ttk.Label(container, text=unit).grid(row=row, column=3, sticky='ew')
    return text_var


def serial_num_entry(container, row, col, def_snum, switch_pos):
    """Creates a serial number entry with channel number and switch position."""
    snum_frame = ttk.Frame(container)
    serial_num_ent = ttk.Entry(snum_frame, font=ENTRY_FONT, width=20)
    serial_num_ent.pack(side="left", fill="both", expand=True)
    switch_pos_ent = tk.IntVar()
    tk.Spinbox(snum_frame, from_=0, to=16, textvariable=switch_pos_ent, width=2,
               state="readonly").pack(side="left", fill="both", expand=True)
    if switch_pos is None:
        switch_pos = 0
    switch_pos_ent.set(str(switch_pos))
    snum_frame.grid(row=row, column=col, sticky='ew')
    serial_num_ent.insert(0, def_snum)
    return serial_num_ent, switch_pos_ent, snum_frame


def remove_snum_entry(snum_frame):
    snum_frame.grid_forget()


def lock_widgets(options_frame):
    """Locks the widgets to prevent the user from editing while the program is running."""
    for child in options_frame.options_grid.winfo_children():
        lock(child, "disabled")
    for child in options_frame.fbg_grid.winfo_children():
        lock(child, "disabled")


def lock_main_widgets(main: ttk.Frame):
    for child in main.winfo_children():
        lock(child, "disabled")


def lock(widget, state):
    if "TFrame" in widget.winfo_class():
        for child in widget.winfo_children():
            lock(child, state)
    else:
        widget.config(state=state)


def unlock_widgets(options_frame):
    """Unlocks the widgets."""
    for child in options_frame.options_grid.winfo_children():
        lock(child, "normal")
    for child in options_frame.fbg_grid.winfo_children():
        lock(child, "normal")


def unlock_main_widgets(main: ttk.Frame):
    for child in main.winfo_children():
        lock(child, "normal")


def browse_file(file_label_var):
    """Updates the excel text entry for the selected file."""
    cparser = configparser.ConfigParser()
    cparser.read(PROG_CONFIG_PATH)
    last_dir = cparser.get("Baking", "last_folder")
    try:
        os.mkdir(last_dir)
    except FileExistsError:
        pass
    file_path = filedialog.asksaveasfilename(
        initialdir=last_dir, title="Save Excel File As", filetypes=(("excel files", "*.xlsx"), ("all files", "*.*")))
    try:
        file_label_var.set(os.path.splitext(file_path)[0] + '.xlsx')
    except AttributeError:
        pass


def sort_column(tree, col, descending):
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
    tree.heading(col, command=lambda c=col: sort_column(tree, c, int(not descending)))


def get_all_children_tree(tree: ttk.Treeview, item="") -> List:
    children = tree.get_children(item)
    for child in children:
        children += get_all_children_tree(tree, child)
    return children


def conn_warning(dev):
    """Warn the user that there was an error connecting to a device."""
    mbox.showwarning("Connection Error", "Currently unable to connect to {},".format(dev) +
                     "make sure the device is connected to the computer and the location " +
                     "information is correct.")


def loc_warning(loc_type):
    """Warn the user of an invalid location input."""
    mbox.showwarning(
        "Invalid Location", "Please input an integer corresponding to the {}.".format(loc_type))


def setup_style():
    style = ttk.Style()
    parent_theme = "winnative"
    style.theme_create("main", parent=parent_theme, settings={
        ".": {"configure": {"background": constants.BG_COLOR}},
        "TFrame": {"configure": {"background": constants.BG_COLOR, "margin": [10, 10, 10, 10]}},
        "TButton": {"configure": {"background": constants.BUTTON_COLOR, "font": ('Helvetica', 16),
                                  "foreground": constants.BUTTON_TEXT, "justify": "center"}},
        "Bold.TLabel": {"configure": {"font": ('Helvetica', 18, 'bold')}},
        "TLabel": {"configure": {"font": ('Helvetica', 16), "foreground": constants.TEXT_COLOR}},
        "TEntry": {"configure": {"font": ('Helvetica', 14)},
                   "map":       {"fieldbackground": [("active", constants.ENTRY_COLOR),
                                                     ("disabled", constants.BG_COLOR)],
                                 "foreground": [("active", "black"),
                                                ("disabled", constants.TEXT_COLOR)]}},
        "Treeview": {"configure":
                     {"foreground": constants.Colors.WHITE, "background": constants.BG_COLOR},
                     "map": {"background": [("selected", constants.TABS_COLOR)],
                             "font": [("selected", ('Helvetica', 10, "bold"))],
                             "foreground": [("selected", constants.Colors.BLACK)]}
                     },
        "Treeview.Heading": {"configure": {"foreground": constants.TEXT_COLOR,
                                           "font": {("Helvetica", 12, "bold")}, "sticky": "ew"}},
        "TNotebook": {"configure": {"tabmargins": [10, 10, 10, 2]}},
        "TCheckbutton": {"configre": {"height": 40, "width": 40}},
        "TNotebook.Tab": {
            "configure": {"padding": [10, 4], "font": ('Helvetica', 18),
                          "background": constants.TAB_COLOR},
            "map":       {"background": [("selected", constants.TABS_COLOR)],
                          "font": [("selected", ('Helvetica', 18, "bold"))],
                          "expand": [("selected", [1, 1, 1, 0])]}}})

    style.theme_use("main")
