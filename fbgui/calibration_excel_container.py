import re
import pandas as pd
from typing import List
from fbgui.helpers import make_length
from fbgui import excel_file_controller


class CalibrationExcelContainer:

    def __init__(self, real_point_data_frame: pd.DataFrame, cycles: List[int]):
        super().__init__()
        self.real_point_data_frame = real_point_data_frame
        self.cycles = cycles
        self.wavelength_headers, self.power_headers = excel_file_controller\
            .get_wavelength_power_headers(real_point_data_frame)
        self.temperature_averages = []
        self.deviation_indexes = []
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
        self.add_deviation()

    def add_wavelengths(self, temperatures: List[float], cycle_num: int):
        self.calibration_data_frame["Temperature (K) Cycle {}".format(cycle_num)] = temperatures
        for wavelength_header in self.wavelength_headers:
            wavelengths = self.get_wavelengths(cycle_num, wavelength_header)
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
        header = excel_file_controller.TEMPERATURE_HEADER
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

    def add_deviation(self):
        for i, wavelength_header in enumerate(self.wavelength_headers):
            mean_wavelength = get_mean_wavelength(list(self.real_point_data_frame[wavelength_header]),
                                                  len(self.wavelength_headers), self.number_of_readings)
            print("{} Mean Wavelength: {}".format(wavelength_header, mean_wavelength))
            for j, cycle in enumerate(self.cycles):
                wavelengths = self.get_wavelengths(cycle, wavelength_header)
                fbg_name = fbg_name_from_header(wavelength_header)
                deviation_column_name = "Cycle {} {} Wavelength Deviation (pm.)".format(cycle, fbg_name)
                self.calibration_data_frame[deviation_column_name] = wavelengths
                self.calibration_data_frame[deviation_column_name] -= mean_wavelength
                self.calibration_data_frame[deviation_column_name] *= 1000
                self.deviation_indexes.append(self.calibration_data_frame.columns.tolist().index(deviation_column_name))

    def get_wavelengths(self, cycle_num: int, wavelength_header: str) -> List[float]:
        wavelengths = self.real_point_data_frame[self.real_point_data_frame["Cycle Num"] == cycle_num][wavelength_header]
        return make_length(list(wavelengths), self.number_of_readings)


def fbg_name_from_header(header: str) -> str:
    return re.match("(.*)(?= Wavelength)", header).group(0)


def get_mean_wavelength(wavelengths: List[float], num_fbgs: int, num_temps: int) -> List[float]:
    try:
        mean_wavelengths = []
        count = 0
        mean_wavelength = 0
        for i in range(num_temps):
            for j in range(i, len(wavelengths), num_fbgs):
                mean_wavelength += wavelengths[j]
                count += 1
            mean_wavelengths.append(mean_wavelength / count)
        return mean_wavelengths
    except ZeroDivisionError:
        return []
