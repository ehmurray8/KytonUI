from enum import Enum

BAKING = "Baking"
CAL = "Cal"

OVEN = "Delta Oven"
LASER = "Micron Optics SM125"
SWITCH = "Optical Switch"
TEMP = "LSC Temperature Controller"
DEV_HEADER = "Devices"

BAKE_FID = "Metadata\n"
CAL_FID = "Caldata\n"


class Colors(Enum):
    WHITE = "#f0eff4"
    AZ_WHITE = "#dcedff"
    MED_BLUE = "#0B3C5D"
    SKY_BLUE = "#328CC1"
    GOLD = "#D9B310"
    BLACK = "#1D2731"
    GRAY = "#2b2a29"

    def __init__(self, hex_color):
        self.color = hex_color

    def __str__(self):
        return self.color


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

HEX_COLORS = ["#FFD700", "#008080", "#FF7373", "#FFC0CB",
              "#40E0D0", "#FFA500", "#00FF00", "#468499",
              "#66CDAA", "#FF7F50", "#FF4040", "#B4EEB4",
              "#DAA520", "#FFFF00", "#C0C0C0", "#F0F8FF",
              "#E6E6FA", "#008000", "#FF00FF", "#0099CC"]
