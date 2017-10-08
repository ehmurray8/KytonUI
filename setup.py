import cx_Freeze
import sys
import matplotlib

base = None

if sys.platform == 'win32':
    base = "Win32GUI"
else:
    base = None


executables = [cx_Freeze.Executable("tkinterVid28.py", base=base, icon="fiber.png")]

cx_Freeze.setup(
    name = "KytonUI",
    options = {"build_exe": {"packages":["tkinter","matplotlib"], "include_files":["clienticon.ico"]}},
    version = "0.01",
    description = "Baking and Calibration program for FBGs.",
    executables = executables
    )
