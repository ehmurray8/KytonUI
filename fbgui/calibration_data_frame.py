import re
import pandas as pd
from typing import List
from fbgui.helpers import make_length
from fbgui import excel_file_controller


class CalibrationDataFrame:

    def __init__(self, real_point_data_frame: pd.DataFrame, cycles: List[int]):
        super().__init__()
        self.real_point_data_frame = real_point_data_frame
        self.cycles = cycles
        self.wavelength_headers, self.power_headers = excel_file_controller\
            .get_wavelength_power_headers(real_point_data_frame)
        self.temperature_averages = []
        self.calibration_data_frame = pd.DataFrame()
        self.populate()

    def get_data_frame(self) -> pd.DataFrame:
        return self.calibration_data_frame

    def populate(self):
        for cycle_num in self.cycles:
            temperatures = self.get_temperatures(cycle_num)
            self.add_wavelengths(temperatures, cycle_num)

        self.calibration_data_frame["Mean Temperature (K)"] = \
            make_length(list(self.temperature_averages), len(self.temperature_averages))
        self.add_powers()
        self.calibration_data_frame["Mean Temperature (K) "] = list(self.temperature_averages)

    def add_wavelengths(self, temperatures: List[float], cycle_num: int):
        self.calibration_data_frame["Temperature (K) Cycle {}".format(cycle_num)] = temperatures
        for wavelength_header in self.wavelength_headers:
            wavelengths = \
                self.real_point_data_frame[self.real_point_data_frame["Cycle Num"] == cycle_num][wavelength_header]
            wavelengths = make_length(list(wavelengths), len(self.temperature_averages))
            delta_wavelengths = [(wavelength - wavelengths[0]) * 1000 for wavelength in wavelengths]
            self.calibration_data_frame["{} Cycle {}".format(wavelength_header, cycle_num)] = wavelengths
            fbg_name = re.match("(.*)(?= Wavelength)", wavelength_header).group(0)
            self.calibration_data_frame["{} {} Wavelength (pm) Cycle {}".format(fbg_name, u"\u0394", cycle_num)] = \
                delta_wavelengths

    def add_powers(self):
        for cycle_num in self.cycles:
            header = excel_file_controller.TEMPERATURE_HEADER
            temperatures = list(
                self.real_point_data_frame[self.real_point_data_frame["Cycle Num"] == cycle_num][header])
            temperatures = make_length(list(temperatures), len(self.temperature_averages))
            self.calibration_data_frame["Temperature (K) Cycle {} ".format(cycle_num)] = temperatures
            for power_header in self.power_headers:
                powers = self.real_point_data_frame[self.real_point_data_frame["Cycle Num"] == cycle_num][power_header]
                powers = make_length(list(powers), len(self.temperature_averages))
                self.calibration_data_frame["{} Cycle {}".format(power_header, cycle_num)] = powers

    def get_temperatures(self, cycle_num: int):
        header = excel_file_controller.TEMPERATURE_HEADER
        temperatures = list(
                self.real_point_data_frame[self.real_point_data_frame["Cycle Num"] == cycle_num][header])
        if not len(self.temperature_averages):
            self.temperature_averages = temperatures
        else:
            temperatures += [0] * (len(self.temperature_averages) - len(temperatures))
            self.temperature_averages = [(t + new_t)/2. if new_t != 0 else t for t, new_t in
                                         zip(self.temperature_averages, temperatures)]
        return make_length(list(temperatures), len(self.temperature_averages))
