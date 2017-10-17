import cx_Freeze
import sys
import os
import matplotlib

os.environ['TCL_LIBRARY'] = "C:\\Users\\Emmet\\AppData\\Local\\Programs\\Python\\Python36\\tcl\\tcl8.6"
os.environ['TK_LIBRARY'] = "C:\\Users\\Emmet\\AppData\\Local\\Programs\\Python\\Python36\\tcl\\tk8.6"

base = None

if sys.platform == 'win32':
    base = "Win32GUI"

executables = [cx_Freeze.Executable("main_program.py", base=base, icon="fiber.png")]

cx_Freeze.setup(
    name = "BakingCalUI",
    options = {"build_exe": {"packages":["tkinter","matplotlib"], "include_files":["fiber.png", "devices.cfg", "docs_icon.png"]}},
    version = "0.01",
    description = "GUI for data collection of baking and calibrating of FBGs.",
    executables = executables
    )
