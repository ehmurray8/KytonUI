"""UI Helper methods."""
import tkinter as tk
from tkinter import ttk
import file_helper
import ui_helper

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
    #ttk.Label(container, text="Switch position:").grid(row=row, column=5, sticky='ew')
    switch_pos_ent = tk.IntVar()
    #tk.Spinbox(container, from_=1, to=4, textvariable=switch_pos_ent, width=width, state="readonly") \
    #        .grid(row=row, column=6, sticky='ew')
    chan_num_ent.set(def_channel)
    #switch_pos_ent.set(def_switch)
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

def array_entry(container, label_text, row, width, height, default_arr=None):
    string_var = tk.StringVar()
    ttk.Label(container, text=label_text).grid(row=row, column=0, sticky='ew')
    text = tk.Text(container, width=width, height=height)
    text.grid(row=row, column=2, sticky='ew')

    text.delete(1.0, tk.END)
    if default_arr is not None:
        text.insert(1.0, str(default_arr))
    return text

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

def open_center(width, height, root):
    #pylint:disable=global-statement
    """Open num fiber dialog in center of the screen."""
    width_screen = root.winfo_screenwidth()
    height_screen = root.winfo_screenheight()

    x_cord = (width_screen/2) - (width/2)
    y_cord = (height_screen/2) - (height/2)

    root.geometry("{}x{}-{}+{}".format(int(width), int(height),\
                             int(x_cord), int(y_cord)))


def update_config(prog):
    """Updates devices configuration."""
    cont_loc, oven_loc, gp700_loc, sm125_addr, sm125_port = file_helper.get_config(prog)

    old_conf = [cont_loc, oven_loc, gp700_loc, sm125_addr, sm125_port]

    popup = tk.Toplevel()
    popup.wm_title("Device Configuration")
    frame = tk.Frame(popup)
    frame.pack()
    config_grid = tk.Frame(frame)
    config_grid.pack(side="top", fill="both", expand=True, padx=10)

    ttk.Label(config_grid, text="340 Controller GPIB0 Port:").grid(row=0, padx=5)
    cont_ent = ttk.Entry(config_grid)
    cont_ent.grid(row=0, column=1, padx=5)
    cont_ent.insert(0, str(cont_loc))

    ttk.Label(config_grid, text="Dicon Oven GPIB0 Port:").grid(row=1, padx=5)
    oven_ent = ttk.Entry(config_grid)
    oven_ent.grid(row=1, column=1, padx=5)
    oven_ent.insert(0, str(oven_loc))

    ttk.Label(config_grid, text="GP700 Switch GPIB0 Port:").grid(row=2, padx=5)
    gp700_ent = ttk.Entry(config_grid)
    gp700_ent.grid(row=2, column=1, padx=5)
    gp700_ent.insert(0, str(gp700_loc))

    ttk.Label(config_grid, text="SM125 IP Address:").grid(row=3, padx=5)
    sm125_addr_ent = ttk.Entry(config_grid)
    sm125_addr_ent.grid(row=3, column=1, padx=5)
    sm125_addr_ent.insert(0, str(sm125_addr))

    ttk.Label(config_grid, text="SM125 IP Port:").grid(row=4, padx=5)
    sm125_port_ent = ttk.Entry(config_grid)
    sm125_port_ent.grid(row=4, column=1, padx=5)
    sm125_port_ent.insert(0, str(sm125_port))


    conf_widgets = [cont_ent, oven_ent, gp700_ent, sm125_addr_ent, sm125_port_ent]

    ttk.Button(frame, text="Save", command=lambda: file_helper.save_config(cont_ent, oven_ent, 
            gp700_ent, sm125_addr_ent, sm125_port_ent, popup, prog)). \
            pack(side="top", fill="both", expand=True, pady=10)

    ui_helper.open_center(350, 150, popup)
    popup.protocol("WM_DELETE_WINDOW", lambda: file_helper.on_closing(popup, old_conf, conf_widgets))


def lock_widgets(parent):
    for child in parent.children.values():
        if "Label" not in child.winfo_class() and "Button" not in child.winfo_class() and "Frame" not in child.winfo_class():
            child.config(state=tk.DISABLED)
        elif child.winfo_class() == "Frame": 
            lock_widgets(child)

def unlock_widgets(parent):
    for child in parent.children.values():
        if "Label" not in child.winfo_class() and "Button" not in child.winfo_class() and "Frame" not in child.winfo_class():
            child.config(state=tk.NORMAL)
        elif child.winfo_class() == "Frame":
            unlock_widgets(child)
