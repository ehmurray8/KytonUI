"""Constants used throughout the program."""
import os
from enum import Enum

from PIL import Image

# Program identifiers
BAKING = "Baking"
CAL = "Cal"

# Device identifiers
OVEN = "Delta Oven"
LASER = "Micron Optics SM125"
SWITCH = "Optical Switch"
TEMP = "LSC Temperature Controller"
DEV_HEADER = "Devices"


class Colors(Enum):
    """Colors used in the GUI styling."""
    WHITE = "#f0eff4"
    AZ_WHITE = "#dcedff"
    MED_BLUE = "#0B3C5D"
    SKY_BLUE = "#328CC1"
    GOLD = "#D9B310"
    BLACK = "#1D2731"
    GRAY = "#2b2a29"

    def __init__(self, hex_color: str):
        """
        Defines a color.

        :param hex_color: Contains the hex value string representing the color.
        """
        self.color = hex_color

    def __str__(self):
        return self.color


LOG_BACKGROUND_COLOR = "#38383d"
DISABLED_COLOR = str(Colors.GRAY)
BG_COLOR = str(Colors.BLACK)
TAB_COLOR = str(Colors.SKY_BLUE)
TABS_COLOR = str(Colors.AZ_WHITE)
ENTRY_COLOR = str(Colors.GRAY)
BUTTON_COLOR = str(Colors.GRAY)
TEXT_COLOR = str(Colors.GOLD)
BUTTON_TEXT = str(Colors.BLACK)
ARRAY_ENTRY_COLOR = str(Colors.WHITE)

ENTRY_FONT = ('Helvetica', 14)
ENTRY_SMALL_FONT = ('Helvetica', 11)

# Excel column colors
HEX_COLORS = ["#FFD700", "#008080", "#FF7373", "#FFC0CB",
              "#40E0D0", "#FFA500", "#00FF00", "#468499",
              "#66CDAA", "#FF7F50", "#FF4040", "#B4EEB4",
              "#DAA520", "#FFFF00", "#C0C0C0", "#F0F8FF",
              "#E6E6FA", "#008000", "#FF00FF", "#0099CC",
              "#FAD1D1", "#A3928F", "#BF6A40", "#FFAA00",
              "#AD961F", "#DDFF33", "#66CC00", "#94E085",
              "#94D1B2", "#40AABF", "#4D7FB2", "#9540BF"]

# Main folder paths
ASSETS_PATH = os.path.join("assets")
CONFIG_PATH = os.path.join("config")
DB_DIR = os.path.join("db")

# Database path
DB_PATH = os.path.join(DB_DIR, "program_data.db")

# Matplotlib images, and style
MPL_STYLE_PATH = os.path.join(ASSETS_PATH, "kyton.mplstyle")
PLAY_PATH = os.path.join(ASSETS_PATH, "play.gif")
PAUSE_PATH = os.path.join(ASSETS_PATH, "pause.gif")

# Config file paths
PROG_CONFIG_PATH = os.path.join(CONFIG_PATH, "prog_config.cfg")
DEV_CONFIG_PATH = os.path.join(CONFIG_PATH, "devices.cfg")

# Gui Images
PROGRAM_LOGO_PATH = os.path.join(ASSETS_PATH, "program_logo.png")
CONFIG_IMG_PATH = os.path.join(ASSETS_PATH, "config.png")
GRAPH_PATH = os.path.join(ASSETS_PATH, "graph.png")
FILE_PATH = os.path.join(ASSETS_PATH, "file.png")
DOCS_ICON_PATH = os.path.join(ASSETS_PATH, 'docs_icon.png')
try:
    DOCS_ICON = Image.open(DOCS_ICON_PATH)
except FileNotFoundError:
    try:
        DOCS_ICON = Image.open(os.path.join("fbgui", DOCS_ICON_PATH))
    except FileNotFoundError:
        DOCS_ICON = ""


# Calibration Graphing Constants
DELTA_TIME_HEADER = "{} Time (hr.)".format(u"\u0394")
DELTA_TIME_HEADER1 = "{} Time (hr.) ".format(u"\u0394")
DELTA_TIME_HEADER2 = "{} Time (hr.)  ".format(u"\u0394")
DATE_TIME_HEADER = "Date Time"
TEMPERATURE_HEADER = "Mean Temperature (K)"
DELTA_TEMPERATURE_HEADER = "{}T (K)".format(u"\u0394")
DELTA_TEMPERATURE_HEADER1 = "{}T (K) ".format(u"\u0394")
DELTA_TEMPERATURE_HEADER2 = "{}T (K)  ".format(u"\u0394")
DELTA_TEMPERATURE_HEADER3 = "{}T (K)   ".format(u"\u0394")
MEAN_DELTA_WAVELENGTH_HEADER = "Mean raw {}{} (pm.)".format(u"\u0394", u"\u03BB")
MEAN_DELTA_POWER_HEADER = "Mean raw {}{} (dBm.)".format(u"\u0394", "P")
REAL_POINT_HEADER = "Real Point"
CYCLE_HEADER = "Cycle Num"

CALIBRATION_TEMPERATURE_HEADER = "Mean Temperature (K) {}"

MARKERS = ['star', 'square', 'triangle', 'circle', 'x', 'plus', 'diamond']

CALIBRATION_START_ROW = 2
CALIBRATION_GRAPH_START_ROW = 2
