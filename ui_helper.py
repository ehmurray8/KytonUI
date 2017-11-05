"""UI Helper methods."""
# pylint: disable=import-error, relative-import
import os
from tkinter import ttk, filedialog 
import tkinter as tk 
from PIL import Image, ImageTk
import file_helper


def file_entry(container, label_text, row, width):
    """Creates an entry with a browse button for the excel file."""
    text_var = tk.StringVar()
    ttk.Label(container, text=label_text).grid(row=row, column=0, sticky='ew')
    ttk.Entry(container, textvariable=text_var, width=width)\
       .grid(row=row, column=2, sticky='ew')
    button_image = Image.open('docs_icon.png')
    button_photo = ImageTk.PhotoImage(button_image)

    browse_button = ttk.Button(
        container, image=button_photo, command=lambda: browse_file(text_var),
        width=10)
    browse_button.grid(column=3, row=row, sticky=(tk.E, tk.W), padx=5, pady=5)
    browse_button.image = button_photo
    return text_var


def browse_file(file_label_var):
    """Updates the excel text entry for the selected file."""
    file_path = filedialog.asksaveasfilename(
        initialdir="./", title="Save Excel File As", filetypes=(("excel files", "*.xlsx"),
                                                                ("all files", "*.*")))
    file_label_var.set(os.path.splitext(file_path)[0] + '.xlsx')


def string_entry(container, label_text, row, width, default_str=""):
    """Creates a string entry, and returns a reference to the entry var."""
    text_var = tk.StringVar()
    ttk.Label(container, text=label_text).grid(row=row, column=0, sticky='ew')
    ttk.Entry(container, textvariable=text_var, width=width)\
        .grid(row=row, column=2, sticky='ew')
    text_var.set(default_str)
    return text_var


def serial_num_entry(container, label_text, row, width,
                     default_str="", def_switch=0, def_channel=1):
    # pylint:disable=too-many-arguments
    """Creates a serial number entry with channel number and switch position."""
    serial_num_ent = string_entry(
        container, label_text, row, width, default_str)
    ttk.Label(container, text="Channel number:").grid(
        row=row, column=3, sticky='ew')
    chan_num_ent = tk.IntVar()
    tk.Spinbox(container, from_=1, to=4, textvariable=chan_num_ent, width=width, state="readonly") \
        .grid(row=row, column=4, sticky='ew')
    ttk.Label(container, text="Switch position:").grid(
        row=row, column=5, sticky='ew')
    switch_pos_ent = tk.IntVar()
    tk.Spinbox(container, from_=0, to=16, textvariable=switch_pos_ent, width=width,
               state="readonly").grid(row=row, column=6, sticky='ew')
    chan_num_ent.set(def_channel)
    switch_pos_ent.set(def_switch)
    ttk.Label(container, width=3).grid(row=row, column=7)
    return serial_num_ent, chan_num_ent, switch_pos_ent


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
    # pylint:disable=too-many-arguments
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


# pylint:disable=too-many-arguments
def array_entry(container, label_text, row, width, height, default_arr=None):
    """Creates an entry to import multiline text."""
    ttk.Label(container, text=label_text).grid(row=row, column=0, sticky='ew')
    text = tk.Text(container, width=width, height=height)
    text.grid(row=row, column=2, sticky='ew')

    text.delete(1.0, tk.END)
    if default_arr is not None:
        text.insert(1.0, str(default_arr))
    return text


def format_selected(flag):
    """Format binary as on/off."""
    if flag == 1:
        return "On"
    return "Off"


def open_center(width, height, root):
    # pylint:disable=global-statement
    """Open num fiber dialog in center of the screen."""
    width_screen = root.winfo_screenwidth()
    height_screen = root.winfo_screenheight()

    x_cord = (width_screen / 2) - (width / 2)
    y_cord = (height_screen / 2) - (height / 2)

    root.geometry("{}x{}-{}+{}".format(int(width), int(height),
                                       int(x_cord), int(y_cord)))


# pylint: disable=too-many-locals
def update_config(prog):
    """Updates devices configuration."""
    cont_loc, oven_loc, op_switch_addr, op_switch_port, sm125_addr, sm125_port = \
        file_helper.get_config(prog)

    old_conf = [cont_loc, oven_loc, op_switch_addr,
                op_switch_port, sm125_addr, sm125_port]

    popup = tk.Toplevel()
    popup.wm_title("Device Configuration")
    frame = tk.Frame(popup)
    frame.pack()
    config_grid = tk.Frame(frame)
    config_grid.pack(side="top", fill="both", expand=True, padx=10)

    row_num = 0

    ttk.Label(config_grid, text="340 Controller GPIB0 Number:").grid(
        row=row_num, padx=5)
    cont_ent = ttk.Entry(config_grid)
    cont_ent.grid(row=row_num, column=1, padx=5)
    cont_ent.insert(0, str(cont_loc))
    row_num += 1

    ttk.Label(config_grid, text="Delta Oven GPIB0 Number:").grid(
        row=row_num, padx=5)
    oven_ent = ttk.Entry(config_grid)
    oven_ent.grid(row=row_num, column=1, padx=5)
    oven_ent.insert(0, str(oven_loc))
    row_num += 1

    ttk.Label(config_grid, text="Optical Switch IP Address").grid(
        row=row_num, padx=5)
    op_switch_addr_ent = ttk.Entry(config_grid)
    op_switch_addr_ent.grid(row=row_num, column=1, padx=5)
    op_switch_addr_ent.insert(0, str(op_switch_addr))
    row_num += 1

    ttk.Label(config_grid, text="Optical Switch IP Port").grid(
        row=row_num, padx=5)
    op_switch_port_ent = ttk.Entry(config_grid)
    op_switch_port_ent.grid(row=row_num, column=1, padx=5)
    op_switch_port_ent.insert(0, str(op_switch_port))
    row_num += 1

    ttk.Label(config_grid, text="SM125 IP Address:").grid(row=row_num, padx=5)
    sm125_addr_ent = ttk.Entry(config_grid)
    sm125_addr_ent.grid(row=row_num, column=1, padx=5)
    sm125_addr_ent.insert(0, str(sm125_addr))
    row_num += 1

    ttk.Label(config_grid, text="SM125 IP Port:").grid(row=row_num, padx=5)
    sm125_port_ent = ttk.Entry(config_grid)
    sm125_port_ent.grid(row=row_num, column=1, padx=5)
    sm125_port_ent.insert(0, str(sm125_port))
    row_num += 1

    conf_widgets = [cont_ent, oven_ent, op_switch_addr_ent, op_switch_port_ent,
                    sm125_addr_ent, sm125_port_ent]

    ttk.Button(frame, text="Save",
               command=lambda: file_helper.save_config(cont_ent, oven_ent,
                                                       op_switch_addr_ent, op_switch_port_ent,
                                                       sm125_addr_ent, sm125_port_ent, popup,
                                                       prog)).\
        pack(side="top", fill="both", expand=True, pady=10)

    open_center(325, 250, popup)
    popup.protocol("WM_DELETE_WINDOW", lambda: file_helper.on_closing(
        popup, old_conf, conf_widgets))


def lock_widgets(parent):
    """Locks the widgets to prevent the user from editing while the program is running."""
    for child in parent.children.values():
        if "Label" not in child.winfo_class() and "Button" not in child.winfo_class() \
                and "Frame" not in child.winfo_class():
            child.config(state=tk.DISABLED)
        elif child.winfo_class() == "Frame":
            lock_widgets(child)


def unlock_widgets(parent):
    """Unlocks the widgets."""
    for child in parent.children.values():
        if "Label" not in child.winfo_class() and "Button" not in child.winfo_class() \
                and "Frame" not in child.winfo_class():
            child.config(state=tk.NORMAL)
        elif child.winfo_class() == "Frame":
            unlock_widgets(child)
