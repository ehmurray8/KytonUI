#! Python3
"""Creates MSI file to use to install executable."""

import cx_Freeze
import sys
import os

bdist_msi_options = {
    'init_script': 'install.py',
    }

os.environ['TCL_LIBRARY'] = "C:\\Users\\Emmet\\AppData\\Local\\Programs\\Python\\Python36\\tcl\\tcl8.6"
os.environ['TK_LIBRARY'] = "C:\\Users\\Emmet\\AppData\\Local\\Programs\\Python\\Python36\\tcl\\tk8.6"
#include_files = [r"C:\Users\Emmet\AppData\Local\Programs\Python\Python36\DLLs\tcl86t.dll",
#                 r"C:\Users\Emmet\AppData\Local\Programs\Python\Python36\DLLs\tk86t.dll",
include_files = ["fiber.png", "docs_icon.png", "devices.cfg"]

base = None
if sys.platform == 'win32':
    base = "Win32GUI"

executables = [cx_Freeze.Executable("main_program.py", base=base,
               icon="fiber.png")]

cx_Freeze.setup(
    name = "BakingCalUI",
    options = {"build_exe": {"packages":["tkinter", "winshell", "win32com", "matplotlib"], 
        "include_files":include_files}},#, "init_script": "install.py"}}, 
        #'bdist_msi': bdist_msi_options},
    version = "1.0",
    description = "UI for baking and calibration of FBGs.",
    executables = executables
)
