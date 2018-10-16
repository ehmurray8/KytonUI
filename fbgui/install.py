"""Ensures assets, and helper data is in the correct place."""
import os
import sys
from shutil import copy2


def install():
    """
    Move matplotlib assets to correct folder, ensure db and config folders are on the disc.
    """
    if hasattr(sys, 'frozen'):
        copy2(os.path.join("assets", "kyton.mplstyle"), os.path.join("mpl-data", "stylelib"))
        copy2(os.path.join("assets", "play.gif"), os.path.join("mpl-data", "images"))
        copy2(os.path.join("assets", "pause.gif"), os.path.join("mpl-data", "images"))
    else:
        site_packs = [s for s in sys.path if 'site-packages' in s][0]
        copy2(os.path.join("assets", "kyton.mplstyle"), os.path.join(site_packs, "matplotlib", "mpl-data", "stylelib"))
        copy2(os.path.join("assets", "play.gif"), os.path.join(site_packs, "matplotlib", "mpl-data", "images"))
        copy2(os.path.join("assets", "pause.gif"), os.path.join(site_packs, "matplotlib", "mpl-data", "images"))

    try:
        os.mkdir("db")
    except FileExistsError:
        pass
    try:
        os.mkdir("config")
    except FileExistsError:
        pass


if __name__ == "__main__":
    install()
