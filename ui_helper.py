"""UI Helper methods."""
import tkinter as tk
from tkinter import ttk

def string_entry(container, label_text, row, width, default_str=""):
    """Creates a string entry, and returns a reference to the entry var."""
    text_var = tk.StringVar()
    ttk.Label(container, text=label_text).grid(row=row, column=0, sticky='ew')
    ttk.Entry(container, textvariable=text_var, width=width)\
                .grid(row=row, column=2, sticky='ew')
    text_var.set(default_str)
    return text_var

def serial_num_entry(container, label_text, row, width, \
            default_str="", def_switch=0, def_channel=1):
    #pylint:disable=too-many-arguments
    """Creates a serial number entry with channel number and switch position."""
    serial_num_ent = string_entry(container, label_text, row, width, default_str)
    ttk.Label(container, text="Channel number:").grid(row=row, column=3, sticky='ew')
    chan_num_ent = tk.IntVar()
    tk.Spinbox(container, from_=1, to=4, textvariable=chan_num_ent, width=width, state="readonly") \
            .grid(row=row, column=4, sticky='ew')
    ttk.Label(container, text="Switch position:").grid(row=row, column=5, sticky='ew')
    switch_pos_ent = tk.IntVar()
    tk.Spinbox(container, from_=1, to=4, textvariable=switch_pos_ent, width=width, state="readonly") \
            .grid(row=row, column=6, sticky='ew')
    chan_num_ent.set(def_channel)
    switch_pos_ent.set(def_switch)
    ttk.Label(container, width=3).grid(row=row, column=7)
    return  serial_num_ent, chan_num_ent, switch_pos_ent


def int_entry(container, label_text, row, width, default_int=0):
    """Creates an int entry, and returns a reference to the entry var."""
    text_var = tk.IntVar()
    ttk.Label(container, text=label_text).grid(row=row, column=0, sticky='ew')
    ttk.Entry(container, textvariable=text_var, width=width)\
                .grid(row=row, column=2, sticky='ew')
    text_var.set(default_int)
    return text_var

def double_entry(container, label_text, row, width, default_double=0.0):
    """Creates an double entry, and returns a reference to the entry var."""
    text_var = tk.DoubleVar()
    ttk.Label(container, text=label_text).grid(row=row, column=0, sticky='ew')
    ttk.Entry(container, textvariable=text_var, width=width)\
                .grid(row=row, column=2, sticky='ew')
    text_var.set(default_double)
    return text_var

def time_entry(container, label_text, row, width, unit, default_double=0.0):
    #pylint:disable=too-many-arguments
    """Creates a time entry, and returns a reference to the entry var."""
    text_var = double_entry(container, label_text, row, width, default_double)
    ttk.Label(container, text=unit).grid(row=row, column=3, sticky='ew')
    return text_var

def checkbox_entry(container, label_text, row, checked=True):
    """Creates a checkbox entry, and returns a reference to the entry var."""
    int_var = tk.IntVar()
    ttk.Label(container, text=label_text).grid(row=row, column=0, sticky='ew')
    checkbox = ttk.Checkbutton(container, variable=int_var)
    checkbox.grid(row=row, column=2, sticky='ew')
    if checked:
        checkbox.invoke()
    return int_var

def print_options(app):
    """Prints the selectable options to the screen."""
    print("SM125: " + format_selected(app.sm125_state.get()))
    print("GP700: " + format_selected(app.gp700_state.get()))
    print("Temp340: " + format_selected(app.temp340_state.get()))
    print("Delta Oven: " + format_selected(app.delta_oven_state.get()))
    print("Baking Temp: " + str(app.baking_temp.get()))
    print("File Name: " + str(app.file_name.get()))
    print("Primary Time: " + str(app.prim_time.get()))
    print("Initial Time: " + str(app.init_time.get()))
    print("Num Points: " + str(app.num_pts.get()))
    index = 0
    while index < 4:
        print("SN#" + str(index+1) + ": " + str(app.sn_ents[index].get()))
        index += 1

def format_selected(flag):
    """Format binary as on/off."""
    if flag == 1:
        return "On"
    return "Off"
