import re
from typing import List, Tuple, Callable

import pandas as pd
import numpy.polynomial.polynomial as poly
import numpy as np

from fbgui import excel_file_controller
from fbgui.helpers import make_length
from fbgui.constants import *


def _get_master_temperatures(all_temperatures: List[List[float]]) -> List[float]:
    master_temperatures = []
    for k in range(len(all_temperatures[0])):
        inner_temperatures = []
        for temperatures in all_temperatures:
            inner_temperatures.append(temperatures[k])
        master_temperatures.append(int(sum(inner_temperatures) / len(inner_temperatures)))
    return master_temperatures


class CalibrationExcelContainer:
    def __init__(self, real_point_data_frame: pd.DataFrame, cycles: List[int]):
        super().__init__()
        self.real_point_data_frame = real_point_data_frame
        self.cycles = cycles
        self.wavelength_headers, self.power_headers = excel_file_controller \
            .get_wavelength_power_headers(real_point_data_frame)
        self.temperature_averages = []
        self.deviation_wavelength_indexes = []
        self.deviation_power_indexes = []
        self.mean_wavelength_indexes = []
        self.mean_power_indexes = []
        self.sensitivity_wavelength_indexes = []
        self.sensitivity_power_indexes = []
        self.master_temperature_column = 0
        self.mean_temperature_column = 0

        # Tuple of Square Matrices, 1st matrix is the curve coefficient, 2nd matrix is the derivative coefficients
        # Each coefficient in the form c0(x^n) + ... + cn(x^0)
        self.wavelength_mean_coefficients = ([], [])  # type: Tuple[List[List[float]], List[List[float]]]
        self.power_mean_coefficients = ([], [])  # type: Tuple[List[List[float]], List[List[float]]]

        self.number_of_readings = 0
        self.calibration_data_frame = pd.DataFrame()
        self.populate()

    def get_data_frame(self) -> pd.DataFrame:
        return self.calibration_data_frame

    def populate(self):
        all_temperatures = []
        for cycle_num in self.cycles:
            temperatures = self.get_temperatures(cycle_num)
            all_temperatures.append(temperatures)
            self.add_wavelengths(temperatures, cycle_num)
        mean_temperature_column_name = "Mean Temperature (K)"
        self.calibration_data_frame[mean_temperature_column_name] = \
            make_length(list(self.temperature_averages), self.number_of_readings)
        self.mean_temperature_column = self._get_index(mean_temperature_column_name) + 1

        self.add_powers(all_temperatures[0])

        self.calibration_data_frame["Mean Temperature (K) "] = list(self.temperature_averages)
        self.add_wavelength_deviation()
        self.add_power_deviation()

        self.get_wavelength_sensitivity_coefficients(all_temperatures)
        self.get_power_sensitivity_coefficients(all_temperatures)

        self.plot_master_temperatures(all_temperatures)

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
            self.temperature_averages = [(t + new_t) / 2. if new_t != 0 else t for t, new_t in
                                         zip(self.temperature_averages, temperatures)]
        self.number_of_readings = len(self.temperature_averages)
        return make_length(list(temperatures), self.number_of_readings)

    def add_wavelength_deviation(self):
        self._add_deviation(self.wavelength_headers, "Wavelength (nm)", self.mean_wavelength_indexes,
                            self._wavelength_inner_deviation)

    def add_power_deviation(self):
        self._add_deviation(self.power_headers, "Power (db)", self.mean_power_indexes,
                            self._power_inner_deviation)

    def get_wavelength_sensitivity_coefficients(self, temperatures: List[List[float]]):
        self._get_sensitivity_mean_coefficients("Wavelength (nm)", temperatures,
                                                self.wavelength_mean_coefficients, self.sensitivity_wavelength_indexes,
                                                self.wavelength_headers, "Wavelength", "(pm/K)")

    def get_power_sensitivity_coefficients(self, temperatures: List[List[float]]):
        self._get_sensitivity_mean_coefficients("Power (db)", temperatures, self.power_mean_coefficients,
                                                self.sensitivity_power_indexes, self.power_headers, "Power", "(db/K)")

    def _get_sensitivity_mean_coefficients(self, header_specifier: str, all_temperatures: List[List[float]],
                                           coefficients_list: Tuple[List[List[float]], List[List[float]]],
                                           indexes: List[int], headers: List[str], type_specifier: str, units: str):
        if len(all_temperatures[0]) < 3:
            return
        for header in headers:
            fbg_name = fbg_name_from_header(header)
            master_temperatures = _get_master_temperatures(all_temperatures)
            mean_column_name = "{} Mean {}".format(fbg_name, header_specifier)
            y_values = self.calibration_data_frame[mean_column_name][1:]
            mean_temperature_column_name = "Mean Temperature (K)"
            x_values = self.calibration_data_frame[mean_temperature_column_name][1:]

            coefficients = []
            for order in range(1, 4):
                coefficients = poly.polyfit(x_values, y_values, order)
                error = np.sum((poly.polyval(x_values, coefficients) - y_values)**2)
                if error <= 10**-6:
                    break
            derivative_coefficients = poly.polyder(coefficients)

            sensitivity_column_name = "{} {} Sensitivity {}".format(fbg_name, type_specifier, units)
            scalar = 1000 if type_specifier == "Wavelength" else 1
            results = poly.polyval(master_temperatures, derivative_coefficients)
            self.calibration_data_frame[sensitivity_column_name] = results
            self.calibration_data_frame[sensitivity_column_name] *= scalar
            coefficients_list[0].append(list(reversed(coefficients)))
            coefficients_list[1].append(list(reversed(derivative_coefficients)))
            self._add_deviation_index(sensitivity_column_name, indexes)

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

    def plot_master_temperatures(self, all_temperatures: List[List[float]]):
        master_temperatures = _get_master_temperatures(all_temperatures)
        master_temperature_column = "Master Temperatures (K)"
        self.calibration_data_frame[master_temperature_column] = master_temperatures
        self.master_temperature_column = self._get_index(master_temperature_column) + 1


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
