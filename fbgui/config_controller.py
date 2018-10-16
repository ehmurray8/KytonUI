import configparser
from typing import List

from fbgui.constants import *


def get_configured_fbg_names(is_calibration: bool) -> List[str]:
    """
    Get the serial numbers recorded in the prog_config configuration file, under the header
    based on the is_cal parameter

    :param is_calibration: True if program is calibration, False otherwise
    :return: list of serial numbers
    """
    program = BAKING
    if is_calibration:
        program = CAL
    parser = configparser.ConfigParser()
    parser.read(PROG_CONFIG_PATH)
    serial_nums = []
    for i in range(4):
        serial_nums.extend(parser.get(program, "chan{}_fbgs".format(i+1)).split(","))
    serial_nums = [s for s in serial_nums if s != '']
    return serial_nums
