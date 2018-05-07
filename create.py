import os
import winshell
from win32com.client import Dispatch
from shutil import copytree, rmtree
from pathlib import Path


def create_shortcut(desktop_shortcut_name, target_path, exe, icon_path):
    desktop = winshell.desktop()
    path = os.path.join(desktop, desktop_shortcut_name)

    if os.path.isfile(path):
        try:
            os.remove(path)
        except PermissionError:
            pass

    exe = os.path.join(target_path, exe)
    wDir = target

    shell = Dispatch('WScript.Shell')
    shortcut = shell.CreateShortCut(path)
    shortcut.Targetpath = exe
    shortcut.WorkingDirectory = wDir
    shortcut.IconLocation = icon_path
    shortcut.save()

    start_menu = winshell.start_menu()
    path = os.path.join(start_menu, "Programs", "Kyton", "FbgUI.lnk")

    if os.path.isfile(path):
        try:
            os.remove(path)
        except PermissionError:
            pass

    if not os.path.isdir(os.path.join(start_menu, "Programs", "Kyton")):
        os.mkdir(os.path.join(start_menu, "Programs", "Kyton"))

    exe = os.path.join(target_path, "fbgui.exe")
    wDir = target

    shortcut = shell.CreateShortCut(path)
    shortcut.Targetpath = exe
    shortcut.WorkingDirectory = wDir
    shortcut.IconLocation = icon_path
    shortcut.save()


if __name__ == "__main__":
    home = str(Path.home())
    target = os.path.join(home, "AppData", "Local", "Programs", "FbgUI")
    if os.path.isdir(target):
        try:
            rmtree(target)
        except PermissionError:
            pass

    copytree("fbgui", target)

    try:
        rmtree("fbgui")
    except PermissionError:
        pass

    icon = os.path.join(target, "fbgui.exe")
    create_shortcut("FbgUI.lnk", target, "fbgui.exe", icon)
    create_shortcut("FbgReadme.lnk", target, os.path.join("docs", "README.html"), icon)
    create_shortcut("FbgSourceCodeDocs.lnk", target, os.path.join("docs", "index.html"), icon)
