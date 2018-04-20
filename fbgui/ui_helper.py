import configparser
import os
import tkinter as tk
from tkinter import ttk, filedialog

from PIL import Image, ImageTk

from fbgui.constants import ENTRY_FONT, ARRAY_ENTRY_COLOR


def file_entry(container, label_text, row, width, def_file=""):
    """Creates an entry with a browse button for the excel file."""
    text_var = tk.StringVar()
    ttk.Label(container, text=label_text).grid(row=row, column=0, sticky='ew')
    ttk.Entry(container, textvariable=text_var, width=width, font=ENTRY_FONT)\
       .grid(row=row, column=2, columnspan=2, sticky='ew')
    path = os.path.join("assets", 'docs_icon.png')
    button_image = Image.open(path)
    button_photo = ImageTk.PhotoImage(button_image)

    browse_button = ttk.Button(container, image=button_photo, command=lambda: browse_file(text_var), width=10)
    browse_button.grid(column=4, row=row, sticky=(tk.E, tk.W), padx=5, pady=5)
    browse_button.image = button_photo
    text_var.set(def_file)
    return text_var


def browse_file(file_label_var):
    """Updates the excel text entry for the selected file."""
    cparser = configparser.ConfigParser()
    cparser.read(os.path.join("config", "prog_config.cfg"))
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


def string_entry(container, label_text, row, width, default_str=""):
    """Creates a string entry, and returns a reference to the entry var."""
    text_var = tk.StringVar()
    ttk.Label(container, text=label_text).grid(row=row, column=0, sticky='ew')
    ttk.Entry(container, textvariable=text_var, width=width, font=ENTRY_FONT).grid(row=row, column=2, sticky='ew')
    text_var.set(default_str)
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


def int_entry(container, label_text, row, width, default_int=0):
    """Creates an int entry, and returns a reference to the entry var."""
    text_var = tk.IntVar()
    ttk.Label(container, text=label_text).grid(row=row, column=0, sticky='ew')
    ttk.Entry(container, textvariable=text_var, width=width, font=ENTRY_FONT).grid(row=row, column=2, sticky='ew')
    text_var.set(default_int)
    return text_var


def double_entry(container, label_text, row, width, default_double=0.0):
    """Creates an double entry, and returns a reference to the entry var."""
    text_var = tk.DoubleVar()
    ttk.Label(container, text=label_text).grid(row=row, column=0, sticky='ew')
    ent = ttk.Entry(container, textvariable=text_var, width=width, font=ENTRY_FONT)
    ent.grid(row=row, column=2, sticky='ew')
    text_var.set(default_double)
    return text_var


def units_entry(container, label_text, row, width, unit, default_double=0.0):
    """Creates a time entry, and returns a reference to the entry var."""
    text_var = double_entry(container, label_text, row, width, default_double)
    ttk.Label(container, text=unit).grid(row=row, column=3, sticky='ew')
    return text_var


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


def format_selected(flag):
    """Format binary as on/off."""
    if flag == 1:
        return "On"
    return "Off"


def open_center(width, height, root):
    """Open num fiber dialog in center of the screen."""
    width_screen = root.winfo_screenwidth()
    height_screen = root.winfo_screenheight()

    x_cord = (width_screen / 2) - (width / 2)
    y_cord = (height_screen / 2) - (height / 2)

    root.geometry("{}x{}-{}+{}".format(int(width), int(height), int(x_cord), int(y_cord)))


def lock_widgets(options_frame):
    """Locks the widgets to prevent the user from editing while the program is running."""
    for child in options_frame.options_grid.winfo_children():
        lock(child, "disabled")
    for child in options_frame.fbg_grid.winfo_children():
        lock(child, "disabled")


def lock_main_widgets(main: ttk.Frame):
    lock(main.winfo_children()[0].winfo_children()[0], "disabled")


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
    lock(main.winfo_children()[0].winfo_children()[0], "normal")