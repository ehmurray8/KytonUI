"""Helper functions that help setup the ui."""
import configparser
import functools
import os
import tkinter as tk
from tkinter import ttk, filedialog, messagebox as mbox
from typing import List, Union, Tuple, Optional

from PIL import ImageTk
from dateutil import parser

import fbgui.constants as constants
from fbgui import helpers
from fbgui.constants import ENTRY_FONT, ARRAY_ENTRY_COLOR, DOCS_ICON, PROG_CONFIG_PATH
from fbgui.options_frame import OptionsPanel


def ui_entry(var_type, use_func: bool = False):
    """
    Decorator for a standard ui entry input field.

    :param var_type: tkinter variable class to use for the ttk Entry
    :param use_func: If True call the wrapped function
    """

    def _ui_entry(func):
        @functools.wraps(func)
        def _wrapper(container: ttk.Frame, label_text: str, row: int, width: int,
                     default: Union[str, int, float] = None) -> tk.Variable:
            """
            Default behavior for a UI Entry widget.

            :param container: frame to add the widgets to
            :param label_text: text for the accompanying label
            :param row: the row of the grid to add the widgets to
            :param width: the width of the entry widget
            :param default: default value to set the entry widget to
            :return: the tkinter variable storing the value of the entry
            """
            var = var_type()
            ttk.Label(container, text=label_text).grid(row=row, column=0, sticky='ew')
            ttk.Entry(container, textvariable=var, width=width, font=ENTRY_FONT) \
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
    """
    Creates a labeled entry with a browse button for the excel file.

    :param text_var: the variable that will store the entry value
    :param container: the container to add the widgets to
    :param row: the row of the container grid to add the widget to
    """
    docs_photo = ImageTk.PhotoImage(DOCS_ICON)
    browse_button = ttk.Button(container, image=docs_photo, command=lambda: browse_file(text_var), width=10)
    browse_button.grid(column=4, row=row, sticky=(tk.E, tk.W), padx=5, pady=5)
    browse_button.image = docs_photo


@ui_entry(tk.IntVar)
def int_entry() -> tk.IntVar:
    """Creates a labeled entry that looks for an integer value as the input."""
    pass


@ui_entry(tk.DoubleVar)
def double_entry() -> tk.DoubleVar:
    """Creates a labeled entry that looks for a double value as the input."""
    pass


@ui_entry(tk.StringVar)
def string_entry() -> tk.StringVar:
    """Creates a labeled entry that looks for a string value as the input."""
    pass


def checkbox_entry(container: ttk.Frame, label_text: str, row: int, checked: bool = True) -> tk.IntVar:
    """
    Creates a checkbox entry, and returns a reference to the entry var.

    :param container: the container to add the widgets to
    :param label_text: the text to set the label to
    :param row: the row of the container to add the widgets to
    :param checked: If True the widget defaults to being checked
    :return: IntVar referencing the checkbutton
    """
    int_var = tk.IntVar()
    ttk.Label(container, text=label_text).grid(row=row, column=0, sticky='ew')
    checkbox = ttk.Checkbutton(container, variable=int_var, width=5)
    checkbox.grid(row=row, column=2, sticky='ew')
    if checked:
        checkbox.invoke()
    return int_var


def array_entry(container: ttk.Frame, label_text: str, row: int, width: int, height: int,
                default_arr: List = None) -> tk.Text:
    """
    Creates an entry to input multi line text, used for storing array values.

    :param container: frame to add the widgets to
    :param label_text: text to write to the label
    :param row: row of the container to add the widgets to
    :param width: the width of the text widget
    :param height: the height of the text widget
    :param default_arr: If not None, the default array to write to the text widget
    :return: the text widget created
    """
    ttk.Label(container, text=label_text).grid(row=row, column=0, sticky='ew')
    text = tk.Text(container, width=width, height=height, bg=ARRAY_ENTRY_COLOR, font=ENTRY_FONT)
    text.grid(row=row, column=2, sticky='ew', columnspan=2)

    text.delete(1.0, tk.END)
    if default_arr is not None:
        text.insert(1.0, str(default_arr))
    return text


def device_entry(container: ttk.Frame, dev_text: str, loc_str: str, row: int, port_str: Optional[str],
                 loc_var: tk.StringVar, port_var: Optional[tk.StringVar]):
    """
    Creates an entry in the device grid for a device.

    :param container: the frame to add the widgets to
    :param dev_text: the device name used as the label text
    :param loc_str: the string to set the location entry to
    :param row: the row to add the widgets to in the container
    :param port_str: the string to set the port entry to if not None
    :param loc_var: the variable referencing the device location
    :param port_var: If the port_str is not None, the variable referencing the device port
    """
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


def units_entry(container: ttk.Frame, label_text: str, row: int, width: int, unit: str,
                default_double: float = 0.0) -> tk.DoubleVar:
    """
    Creates a time entry, and returns a reference to the entry var.

    :param container: the frame to add the widgets to
    :param label_text: the text to write to the label
    :param row: the row of the container grid to add the widgets to
    :param width: the width of the entry widget
    :param unit: the string representing the unit the values of the entry are in
    :param default_double: the default value to use for the widget
    :return: the DoubleVar referencing the entry
    """
    text_var = double_entry(container, label_text, row, width, default_double)
    ttk.Label(container, text=unit).grid(row=row, column=3, sticky='ew')
    return text_var


def extra_point_entry(container: ttk.Frame, label_text: str, row: int, temperature_value: float) -> \
        Tuple[tk.DoubleVar, tk.Text, tk.Text]:
    ttk.Label(container, text=label_text).grid(row=row, column=0, sticky='ew')
    temperature = tk.DoubleVar()
    entry_frame = ttk.Frame(container)
    entry_frame.grid(row=row, column=2, columnspan=3, sticky='nsew')
    temperature.set(temperature_value)

    ttk.Entry(entry_frame, textvariable=temperature, width=10, font=ENTRY_FONT) \
        .pack(side=tk.LEFT, expand=True, fill=tk.BOTH)
    ttk.Label(entry_frame, text="K").pack(side=tk.LEFT, padx=5)

    wavelength_text = tk.Text(entry_frame, width=30, height=4, bg=ARRAY_ENTRY_COLOR, font=constants.ENTRY_SMALL_FONT)
    wavelength_text.pack(side=tk.LEFT)
    wavelength_label = ttk.Label(entry_frame, text="nm")
    wavelength_label.pack(side=tk.LEFT, padx=5)
    wavelength_label.bind("<Button-1>", lambda e: show_entries(e, "Wavelength (nm) @ {}", temperature, wavelength_text))

    power_text = tk.Text(entry_frame, width=25, height=4, bg=ARRAY_ENTRY_COLOR, font=constants.ENTRY_SMALL_FONT)
    power_text.pack(side=tk.LEFT)
    power_label = ttk.Label(entry_frame, text="dB")
    power_label.pack(side=tk.LEFT, padx=5)
    power_label.bind("<Button-1>", lambda e: show_entries(e, "Power (dB) @ {}", temperature, wavelength_text))
    return temperature, wavelength_text, power_text


def show_entries(_, title: str, temperature: tk.DoubleVar, values_entry: tk.Text):
    title_str = title.format(temperature.get())
    try:
        mbox.showinfo("Extra Point Viewer", "{}\n{}"
                      .format(title_str, "\n".join("{}. {}".format(i+1, x)
                                                   for i, x in enumerate(values_entry.get(1.0, tk.END).split(",")))))
    except ValueError:
        mbox.showwarning(title_str, "Text in the field is misformatted, please update the values.")


def serial_num_entry(container: ttk.Frame, row: int, col: int, def_snum: str,
                     switch_pos: Optional[int]) -> Tuple[ttk.Entry, tk.IntVar, ttk.Frame, tk.IntVar]:
    """
    Creates a serial number entry with channel number and switch position.

    :param container: the frame to add the widgets to
    :param row: the row of the container grid to add the widgets to
    :param col: the column of the container grid to add the widgets to
    :param def_snum: the default name of the serial number being added
    :param switch_pos: the default switch position, if None then use 0 as the switch position
    :return: serial number entry widget, IntVar referencing the switch position spinbox, the frame containing
             the serial number entry and switch position switchbox for a FBG, and an IntVar referencing the
             CheckButton
    """
    snum_frame = ttk.Frame(container)
    serial_num_ent = ttk.Entry(snum_frame, font=ENTRY_FONT, width=20)
    serial_num_ent.pack(side="left", fill="both", expand=True)
    switch_pos_ent = tk.IntVar()
    tk.Spinbox(snum_frame, from_=0, to=16, textvariable=switch_pos_ent, width=2,
               state="readonly").pack(side="left", fill="both", expand=True)
    if switch_pos is None:
        switch_pos = 0
    selected = tk.IntVar()
    tk.Checkbutton(snum_frame, variable=selected).pack(side="left")
    selected.set(0)
    switch_pos_ent.set(str(switch_pos))
    snum_frame.grid(row=row, column=col, sticky='ew')
    serial_num_ent.insert(0, def_snum)
    return serial_num_ent, switch_pos_ent, snum_frame, selected


def remove_snum_entry(snum_frame):
    """Remove a serial number frame."""
    snum_frame.grid_forget()


def lock_widgets(options_frame: OptionsPanel):
    """
    Locks the widgets to prevent the user from editing while the program is running. Lock all the widgets
    in the options_grid and the fbg_grid of the options_panel.

    :param options_frame: options screen wrapper
    """
    for child in options_frame.options_grid.winfo_children():
        lock(child, "disabled")
    for child in options_frame.fbg_grid.winfo_children():
        lock(child, "disabled")


def lock_main_widgets(main: ttk.Frame):
    """
    Lock all of the widgets on the main device frame.

    :param main: the main device frame
    """
    for child in main.winfo_children():
        lock(child, "disabled")


def lock(widget: tk.Widget, state: str):
    """
    Either lock or unlock a widget based on the state string.

    :param widget: recursively lock/unlock if its a frame otherwise change the config to the specified state
    :param state: state to set the widgets to
    """
    if "TFrame" in widget.winfo_class():
        for child in widget.winfo_children():
            lock(child, state)
    else:
        widget.config(state=state)


def unlock_widgets(options_frame: OptionsPanel):
    """
    Unlocks the widgets.

    :param options_frame: options screen wrapper, unlock all widgets in the options_frame
    """
    for child in options_frame.options_grid.winfo_children():
        lock(child, "normal")
    for child in options_frame.fbg_grid.winfo_children():
        lock(child, "normal")


def unlock_main_widgets(main: ttk.Frame):
    """
    Unlock all the widgets in the main device frame.

    :param main: main device frame on the home screen
    """
    for child in main.winfo_children():
        lock(child, "normal")


def browse_file(file_label_var: tk.StringVar):
    """
    Updates the excel text entry for the selected file, using the filedialog.

    :param file_label_var: the file label variable referencing the file input entry on the options screen
    """
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


def sort_column(tree: ttk.Treeview, col: int, descending: bool):
    """
    Sort tree contents when a column header is clicked on.

    :param tree: the root tree to sort
    :param col: the column of the tree to sort
    :param descending: If True sort in descending order, otherwise sort in ascending order
    """
    data = [(tree.set(child, col), child) for child in tree.get_children('')]
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

    data.sort(reverse=descending)
    for ix, item in enumerate(data):
        tree.move(item[1], '', ix)
    tree.heading(col, command=lambda c=col: sort_column(tree, c, not descending))


def get_all_children_tree(tree: ttk.Treeview, item: str = "") -> List:
    """
    Get all of the children of item.

    :param tree: treeview to look through
    :param item: parent element to recursively look for children from
    :return: List of all of the children of item
    """
    children = tree.get_children(item)
    for child in children:
        children += get_all_children_tree(tree, child)
    return children


def conn_warning(dev: str):
    """
    Warn the user that there was an error connecting to a device.

    :param dev: the device identifier string
    """
    mbox.showwarning("Connection Error", "Currently unable to connect to {},".format(dev) +
                     "make sure the device is connected to the computer and the location " +
                     "information is correct.")


def loc_warning(loc_type: str):
    """
    Warn the user of an invalid location input.

    :param loc_type: string identifying what type of connection is attempting to be made
    """
    mbox.showwarning(
        "Invalid Location", "Please input an integer corresponding to the {}.".format(loc_type))


def setup_style():
    """Sets up the main style of the program."""
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
                   "map": {"fieldbackground": [("active", constants.ENTRY_COLOR),
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
            "map": {"background": [("selected", constants.TABS_COLOR)],
                    "font": [("selected", ('Helvetica', 18, "bold"))],
                    "expand": [("selected", [1, 1, 1, 0])]}}})

    style.theme_use("main")
