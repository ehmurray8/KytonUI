import os, winshell
import shutil
import getpass
from win32com.client import Dispatch

def create():
    """Creates a Windows start menu shortcut."""
    desktop = winshell.desktop()
    path = os.path.join(desktop, "BakingCalUI.lnk")
    target = "..\\main_program.exe"
    wDir = "..\\"
    icon = "..\\assets\\fiber.ico"

    shell = Dispatch('WScript.Shell')
    shortcut = shell.CreateShortCut(path)
    shortcut.Targetpath = target
    shortcut.WorkingDirectory = wDir
    shortcut.IconLocation = icon
    shortcut.save()

    username = getpass.getuser()
    start_menu_path = "C:\\Users\\{}\\AppData\\Roaming\\Microsoft\\Windows\\Start Menu\\BakingCalUI.lnk" \
                      .format(username)
    shutil.move(path, start_menu_path)

if __name__ == "__main__":
    create()
