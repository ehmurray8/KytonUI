import cx_Freeze
import sys
import os

#os.environ['TCL_LIBRARY'] = "C:\\Users\\phils\\AppData\\Local\\Programs\\Python362\\tcl\\tcl8.6"
#os.environ['TK_LIBRARY'] = "C:\\Users\\phils\\AppData\\Local\\Programs\\Python362\\tcl\\tk8.6"

os.environ['TCL_LIBRARY'] = "C:\\Users\\Emmet\\AppData\\Local\\Programs\\Python36\\tcl\\tcl8.6"
os.environ['TK_LIBRARY'] = "C:\\Users\\Emmet\\AppData\\Local\\Programs\\Python36\\tcl\\tk8.6"

base = None
if sys.platform == 'win32':
    base = "Win32GUI"

assets = os.path.join("fbgui", "assets")
executables = [cx_Freeze.Executable(os.path.join("fbgui", "main_program.py"), base=base,
                                    icon=os.path.join(assets, "fiber.png"),
               shortcutName="BakingCalUI", shortcutDir='ProgramMenuFolder')]

asset_files = [os.path.join(assets, fname) for fname in ["fiber.png", "plus.png", "minus.png", "config.png",
                                                         "graph.png", "docs_icon.png"]]
include_files = [os.path.join("fbgui", "config", "devices.cfg")]
include_files.extend(asset_files)


bdist_msi_options = {
    "upgrade_code": "{96a85bac-52af-4019-9e94-3afcc9e1ad0c}",
    'add_to_path': False,
    'initial_target_dir': r'[ProgramFilesFolder]{}'.format("BakingCalUI"),
}

cx_Freeze.setup(
    name="BakingCalUI",
    options={
        "build_exe": {
            "packages": ["tkinter", "matplotlib", "pandas", "numpy", "StyleFrame", "sqlite3"],
            "include_files": include_files
        }, "bdist_msi": bdist_msi_options
    },
    version="0.0.1",
    description="GUI for data collection of baking and calibrating of FBGs.",
    executables=executables
)
