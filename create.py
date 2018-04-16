import os, winshell
from win32com.client import Dispatch
from shutil import copytree, rmtree
from pathlib import Path
import configparser
import sys


if __name__ == "__main__":
    home = str(Path.home())
    target = os.path.join(home, "AppData", "Local", "Programs", "FbgUI")
    if os.path.isdir(target):
        try:
            rmtree(target)
        except PermissionError: pass


    CParser = configparser.ConfigParser()
    CParser.read(os.path.join("fbgui", "config.cfg"))

    CParser.add_section("Location")
    CParser.set("Location", "directory", str(os.path.dirname(sys.executable)))

    with open(os.path.join("fbgui", "config.cfg"), "w") as dcfg:
        CParser.write(dcfg)

    copytree("fbgui", target)
    try:
        rmtree("fbgui")
    except PermissionError: pass

    desktop = winshell.desktop()
    path = os.path.join(desktop, "FbgUI.lnk")

    if os.path.isfile(path):
        try:
            os.remove(path)
        except PermissionError: pass

    exe = os.path.join(target, "fbgui.exe")
    wDir = target
    #icon = os.path.join(target, "assets", "fiber.bmp")
    icon = os.path.join(target, "fbgui.exe")

    shell = Dispatch('WScript.Shell')
    shortcut = shell.CreateShortCut(path)
    shortcut.Targetpath = exe
    shortcut.WorkingDirectory = wDir
    shortcut.IconLocation = icon
    shortcut.save()

    start_menu = winshell.start_menu()
    path = os.path.join(start_menu, "Programs", "Kyton", "FbgUI.lnk")

    if os.path.isfile(path):
        try:
            os.remove(path)
        except PermissionError: pass

    if not os.path.isdir(os.path.join(start_menu, "Programs", "Kyton")):
        os.mkdir(os.path.join(start_menu, "Programs", "Kyton"))

    exe = os.path.join(target, "fbgui.exe")
    wDir = target
    #icon = os.path.join(target, "assets", "fiber.bmp")
    icon = os.path.join(target, "fbgui.exe")

    shortcut = shell.CreateShortCut(path)
    shortcut.Targetpath = exe
    shortcut.WorkingDirectory = wDir
    shortcut.IconLocation = icon
    shortcut.save()
