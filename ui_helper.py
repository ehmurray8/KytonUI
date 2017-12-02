"""UI Helper methods."""
# pylint: disable=import-error, relative-import
import os
from tkinter import ttk, filedialog 
import tkinter as tk 
from PIL import Image, ImageTk

ENTRY_FONT = ('Helvetica', 14)


def file_entry(container, label_text, row, width):
    """Creates an entry with a browse button for the excel file."""
    text_var = tk.StringVar()
    ttk.Label(container, text=label_text).grid(row=row, column=0, sticky='ew')
    ttk.Entry(container, textvariable=text_var, width=width, font=ENTRY_FONT)\
       .grid(row=row, column=2, sticky='ew')
    button_image = Image.open('assets\docs_icon.png')
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
    try:
        file_label_var.set(os.path.splitext(file_path)[0] + '.xlsx')
    except AttributeError:
        pass


def string_entry(container, label_text, row, width, default_str=""):
    """Creates a string entry, and returns a reference to the entry var."""
    text_var = tk.StringVar()
    ttk.Label(container, text=label_text).grid(row=row, column=0, sticky='ew')
    ttk.Entry(container, textvariable=text_var, width=width, font=ENTRY_FONT)\
        .grid(row=row, column=2, sticky='ew')
    text_var.set(default_str)
    return text_var


def serial_num_entry(container, row, col, def_snum):
    # pylint:disable=too-many-arguments
    """Creates a serial number entry with channel number and switch position."""
    snum_frame = ttk.Frame(container)
    serial_num_ent = ttk.Entry(snum_frame, font=ENTRY_FONT, width=20)
    serial_num_ent.pack(side="left", fill="both", expand=True)
    switch_pos_ent = tk.IntVar()
    tk.Spinbox(snum_frame, from_=0, to=16, textvariable=switch_pos_ent, width=2,
               state="readonly").pack(side="left", fill="both", expand=True)
    switch_pos_ent.set("0")
    #ttk.Label(container, width=3).grid(row=row, column=7)
    snum_frame.grid(row=row, column=col, sticky='ew')
    return serial_num_ent, switch_pos_ent


def int_entry(container, label_text, row, width, default_int=0):
    """Creates an int entry, and returns a reference to the entry var."""
    text_var = tk.IntVar()
    ttk.Label(container, text=label_text).grid(row=row, column=0, sticky='ew')
    ttk.Entry(container, textvariable=text_var, width=width, font=ENTRY_FONT)\
        .grid(row=row, column=2, sticky='ew')
    text_var.set(default_int)
    return text_var


def double_entry(container, label_text, row, width, default_double=0.0):
    """Creates an double entry, and returns a reference to the entry var."""
    text_var = tk.DoubleVar()
    ttk.Label(container, text=label_text).grid(row=row, column=0, sticky='ew')
    ttk.Entry(container, textvariable=text_var, width=width, font=ENTRY_FONT)\
        .grid(row=row, column=2, sticky='ew')
    text_var.set(default_double)
    return text_var


def units_entry(container, label_text, row, width, unit, default_double=0.0):
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
def array_entry(container, label_text, row, width, height, color, default_arr=None):
    """Creates an entry to import multiline text."""
    ttk.Label(container, text=label_text).grid(row=row, column=0, sticky='ew')
    text = tk.Text(container, width=width, height=height, bg=color, font=ENTRY_FONT)
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


def lock_widgets(parent):
    """Locks the widgets to prevent the user from editing while the program is running."""
    try:
        for child in parent.winfo_children:#.values():
            if "Label" not in child.winfo_class() and "Button" not in child.winfo_class() \
                    and "Frame" not in child.winfo_class():
                #child.config(state=tk.DISABLED)
                child.state(["disabled"])
            elif child.winfo_class() == "Frame":
                lock_widgets(child)
    except Exception as e:
        print(str(e))
        pass


def unlock_widgets(parent):
    """Unlocks the widgets."""
    for child in parent.children.values():
        if "Label" not in child.winfo_class() and "Button" not in child.winfo_class() \
                and "Frame" not in child.winfo_class():
            child.config(state=tk.NORMAL)
        elif child.winfo_class() == "Frame":
            unlock_widgets(child)
