import re
from typing import List, Tuple, Callable

import pandas as pd

from fbgui import excel_file_controller
from fbgui.helpers import make_length
from fbgui.constants import *


class CalibrationExcelContainer:

    def __init__(self, real_point_data_frame: pd.DataFrame, cycles: List[int]):
        super().__init__()
        self.real_point_data_frame = real_point_data_frame
        self.cycles = cycles
        self.wavelength_headers, self.power_headers = excel_file_controller\
            .get_wavelength_power_headers(real_point_data_frame)
        self.temperature_averages = []
        self.deviation_wavelength_indexes = []
        self.deviation_power_indexes = []
        self.mean_wavelength_indexes = []
        self.mean_power_indexes = []
        self.number_of_readings = 0
        self.calibration_data_frame = pd.DataFrame()
        self.populate()

    def get_data_frame(self) -> pd.DataFrame:
        return self.calibration_data_frame

    def populate(self):
        temperatures = []
        for cycle_num in self.cycles:
            temperatures = self.get_temperatures(cycle_num)
            self.add_wavelengths(temperatures, cycle_num)

        self.calibration_data_frame["Mean Temperature (K)"] = \
            make_length(list(self.temperature_averages), self.number_of_readings)
        self.add_powers(temperatures)
        self.calibration_data_frame["Mean Temperature (K) "] = list(self.temperature_averages)
        self.add_wavelength_deviation()
        self.add_power_deviation()

    def add_wavelengths(self, temperatures: List[float], cycle_num: int):
        self.calibration_data_frame["Temperature (K) Cycle {}".format(cycle_num)] = temperatures
        for wavelength_header in self.wavelength_headers:
            wavelengths = self.get_readings(cycle_num, wavelength_header)
            delta_wavelengths = [(wavelength - wavelengths[0]) * 1000 for wavelength in wavelengths]
            self.calibration_data_frame["{} Cycle {}".format(wavelength_header, cycle_num)] = wavelengths
            fbg_name = fbg_name_from_header(wavelength_header)
            self.calibration_data_frame["{} {} Wavelength (pm) Cycle {}".format(fbg_name, u"\u0394", cycle_num)] = \
                delta_wavelengths

    def add_powers(self, temperatures: List[float]):
        for cycle_num in self.cycles:
            self.calibration_data_frame["Temperature (K) Cycle {} ".format(cycle_num)] = temperatures
            for power_header in self.power_headers:
                powers = self.real_point_data_frame[self.real_point_data_frame["Cycle Num"] == cycle_num][power_header]
                powers = make_length(list(powers), self.number_of_readings)
                self.calibration_data_frame["{} Cycle {}".format(power_header, cycle_num)] = powers

    def get_temperatures(self, cycle_num: int) -> List[float]:
        header = TEMPERATURE_HEADER
        temperatures = list(
                self.real_point_data_frame[self.real_point_data_frame["Cycle Num"] == cycle_num][header])
        if not self.number_of_readings:
            self.temperature_averages = temperatures
        else:
            temperatures += [0] * (self.number_of_readings - len(temperatures))
            self.temperature_averages = [(t + new_t)/2. if new_t != 0 else t for t, new_t in
                                         zip(self.temperature_averages, temperatures)]
        self.number_of_readings = len(self.temperature_averages)
        return make_length(list(temperatures), self.number_of_readings)

    def add_wavelength_deviation(self):
        self._add_deviation(self.wavelength_headers, "Wavelength (nm)", self.mean_wavelength_indexes,
                            self._wavelength_inner_deviation)

    def add_power_deviation(self):
        self._add_deviation(self.power_headers, "Power (db)", self.mean_power_indexes,
                            self._power_inner_deviation)

    def _wavelength_inner_deviation(self, cycle: int, fbg_name: str, wavelength_header: str,
                                    mean_wavelengths: List[float]):
        deviation_column_name = "Cycle {} {} Wavelength Deviation (pm)".format(cycle, fbg_name)
        self.add_deviation_column(deviation_column_name, wavelength_header, cycle, mean_wavelengths)
        self.calibration_data_frame[deviation_column_name] *= 1000
        self._add_deviation_index(deviation_column_name, self.deviation_wavelength_indexes)

    def _power_inner_deviation(self, cycle: int, fbg_name: str, power_header: str, mean_powers: List[float]):
        deviation_column_name = "Cycle {} {} Power Deviation (db)".format(cycle, fbg_name)
        self.add_deviation_column(deviation_column_name, power_header, cycle, mean_powers)
        self._add_deviation_index(deviation_column_name, self.deviation_power_indexes)

    def _add_deviation_index(self, column_name: str, deviation_indexes: List[int]):
        deviation_index = self._get_index(column_name)
        deviation_indexes.append(deviation_index)

    def _add_deviation(self, headers: List[str], header_specifier: str, mean_indexes: List[int],
                       inner_deviation_function: Callable[[int, str, str, List[float]], None]):
        for i, header in enumerate(headers):
            means, fbg_name = self.get_means_and_fbg_name(header)
            mean_deviation_column_name = "{} Mean {}".format(fbg_name, header_specifier)
            self.calibration_data_frame[mean_deviation_column_name] = means
            mean_index = self._get_index(mean_deviation_column_name)
            mean_indexes.append(mean_index)
            for cycle in self.cycles:
                inner_deviation_function(cycle, fbg_name, header, means)

    def get_means_and_fbg_name(self, header) -> Tuple[List[float], str]:
        means = get_means_at_temperatures(list(self.real_point_data_frame[header]), self.number_of_readings)
        fbg_name = fbg_name_from_header(header)
        return means, fbg_name

    def add_deviation_column(self, deviation_column_name: str, header: str, cycle: int, means: List[float]):
        readings = self.get_readings(cycle, header)
        self.calibration_data_frame[deviation_column_name] = readings
        self.calibration_data_frame[deviation_column_name] -= means

    def _get_index(self, column_name: str) -> int:
        return self.calibration_data_frame.columns.tolist().index(column_name)

    def get_readings(self, cycle_num: int, header: str) -> List[float]:
        readings = \
            self.real_point_data_frame[self.real_point_data_frame["Cycle Num"] == cycle_num][header]
        return make_length(list(readings), self.number_of_readings)


def fbg_name_from_header(header: str) -> str:
    name_match = re.match("(.*)(?= Wavelength)", header)
    if name_match is None:
        name_match = re.match("(.*)(?= Power)", header)
    return name_match.group(0)


def get_means_at_temperatures(values: List[float], num_temps: int) -> List[float]:
    try:
        means = []
        for i in range(num_temps):
            count = 0
            mean = 0
            for j in range(i, len(values), num_temps):
                mean += values[j]
                count += 1
            means.append(mean / count)
        return means
    except ZeroDivisionError:
        return []

