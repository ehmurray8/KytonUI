import sys
import os
from shutil import copy2, rmtree
import configparser


def install():
    if hasattr(sys, 'frozen'):
        copy2(os.path.join("assets", "kyton.mplstyle"), os.path.join("mpl-data", "stylelib"))
        copy2(os.path.join("assets", "play.gif"), os.path.join("mpl-data", "images"))
        copy2(os.path.join("assets", "pause.gif"), os.path.join("mpl-data", "images"))
        try:
            os.mkdir("db")
        except FileExistsError:
            pass

        cparser = configparser.ConfigParser()
        cparser.read(os.path.join("config.cfg"))

        try:
            directory = cparser.get("Location", "directory")
            rmtree(directory)
        except configparser.NoSectionError:
            pass
        except PermissionError:
            pass
        except FileNotFoundError:
            pass
    else:
        site_packs = [s for s in sys.path if 'site-packages' in s][0]
        copy2(os.path.join("assets", "kyton.mplstyle"), os.path.join(site_packs, "matplotlib", "mpl-data", "stylelib"))
        copy2(os.path.join("assets", "play.gif"), os.path.join(site_packs, "matplotlib", "mpl-data", "images"))
        copy2(os.path.join("assets", "pause.gif"), os.path.join(site_packs, "matplotlib", "mpl-data", "images"))
        try:
            os.mkdir("db")
            os.mkdir("config")
        except FileExistsError:
            pass


if __name__ == "__main__":
    install()
