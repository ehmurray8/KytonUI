import os
import winshell
from win32com.client import Dispatch
from shutil import copytree, rmtree, move
from pathlib import Path


def create_shortcut(desktop_shortcut_name, target_path, exe, icon_path):
    desktop = winshell.desktop()
    path = os.path.join(desktop, desktop_shortcut_name)

    remove_file(path)

    exe = os.path.join(target_path, exe)
    create_shortcut_file(path, exe, target_path, icon_path)

    start_menu = winshell.start_menu()
    path = os.path.join(start_menu, "Programs", "Kyton", "FbgUI.lnk")

    remove_file(path)

    if not os.path.isdir(os.path.join(start_menu, "Programs", "Kyton")):
        os.mkdir(os.path.join(start_menu, "Programs", "Kyton"))

    exe = os.path.join(target_path, "fbgui.exe")
    create_shortcut_file(path, exe, target_path, icon_path)


def create_shortcut_file(path, exe, working_directory, icon_path):
    shortcut = SHELL.CreateShortCut(path)
    shortcut.Targetpath = exe
    shortcut.WorkingDirectory = working_directory
    shortcut.IconLocation = icon_path
    shortcut.save()


def remove_file(path: str):
    if os.path.isfile(path):
        try:
            os.remove(path)
        except PermissionError:
            pass


def remove_old_installation(target_path):
    if os.path.isdir(target_path):
        try:
            rmtree(target_path)
        except PermissionError:
            pass


def save_config_files(root_path, target_path):
    config_location = os.path.join(target_path, "config")
    db_location = os.path.join(target_path, "db")
    old_config_location = os.path.join(root_path, "config")
    old_db_location = os.path.join(root_path, "db")
    if os.path.isdir(old_config_location):
        rmtree(old_config_location)
    if os.path.isdir(old_db_location):
        rmtree(old_db_location)
    if os.path.isdir(config_location):
        copytree(config_location, old_config_location)
    if os.path.isdir(db_location):
        copytree(db_location, old_db_location)


def restore_config_files(root_path, target_path):
    config_location = os.path.join(root_path, "config")
    db_location = os.path.join(root_path, "db")
    if os.path.isdir(config_location):
        move(config_location, target_path)
    if os.path.isdir(db_location):
        move(db_location, target_path)


if __name__ == "__main__":
    home = str(Path.home())
    ROOT = os.path.join(home, "AppData", "Local", "Programs")
    TARGET = os.path.join(ROOT, "FbgUI")
    SHELL = Dispatch('WScript.Shell')

    save_config_files(ROOT, TARGET)
    remove_old_installation(TARGET)
    copytree("fbgui", TARGET)
    restore_config_files(ROOT, TARGET)

    try:
        rmtree("fbgui")
    except PermissionError:
        pass

    ICON = os.path.join(TARGET, "fbgui.exe")
    create_shortcut("FbgUI.lnk", TARGET, "fbgui.exe", ICON)
    create_shortcut("FbgReadme.lnk", TARGET, os.path.join("docs", "README.html"), ICON)
