"""Data container for database data."""
from queue import Queue

import numpy as np
import pandas as pd

from fbgui.config_controller import *
from fbgui.messages import MessageType, Message


class DataCollection(object):
    """
    Data container class for data stored in the database for the program

    **Create must be called in order to instantiate the object properly based on a dataframe object.**

    :ivar List[float] times: list of delta times in hours, from the start
    :ivar List[float] temps: list of temperatures in Kelvin
    :ivar List[delta_temps: list of delta temperatures in Kelvin, from the start
    :ivar List[List[float]] powers: 2D list of powers by serial number in dBm.
    :ivar List[List[float]] delta_powers: 2D list of delta powers, from the start, by serial number, in dBm.
    :ivar List[float] mean_delta_powers: list of average delta power in dBm, from the start
    :ivar List[List[float]] wavelengths: 2D list of wavelengths by serial number in nm.
    :ivar List[List[float]] delta_wavelengths: 2D list of delta wavelengths, from the start, by serial number, in pm.
    :ivar List[float] mean_delta_wavelengths: list of average delta wavelengths in pm.
    :ivar List[float] drift_rates: list of calibration drift rates mK/min
    """

    def __init__(self):
        """Create empty collection, must call create to populate."""
        self.times = []  # type: List[float]
        self.temps = []  # type: List[float]
        self.delta_temps = []  # type: List[float]
        self.powers = []  # type: List[List[float]]
        self.delta_powers = []  # type: List[List[float]]
        self.mean_delta_powers = []  # type: List[float]
        self.wavelengths = []  # type: List[List[float]]
        self.delta_wavelengths_pm = []  # type: List[List[float]]
        self.mean_delta_wavelengths_pm = []  # type: List[float]
        self.drift_rates = []  # type: List[float]

    def create(self, is_cal: bool, df: pd.DataFrame, fbg_names: List[str]=None, main_queue: Queue=None):
        """
        Creates a data collection from the given dataframe, updates the instance variables to match how they are
        specified in the class docstring, numpy arrays are used instead of lists however.

        **Adds date time column to the data frame**

        :param is_cal: boolean for whether or not the program is a calibration program
        :param df: dataframe representing the sql table for the program
        :param fbg_names: list of serial numbers that are in use for the program, if None the serial numbers
                    will be found using file_helper get_snums function
        :param main_queue: if present used for writing messages to the program log
        :raises RuntimeError: If the table has not been created or populated yet
        """
        if fbg_names is None:
            fbg_names = get_configured_fbg_names(is_cal)
        try:
            timestamps = df["Date Time"]
            start_time = df["Date Time"][0]
            df['Date Time'] = pd.to_datetime(df['Date Time'], unit="s")
            self.times = [(time - start_time) / 60 / 60 for time in timestamps]
            self.temps = df["Mean Temperature (K)"]
            first_temp = self.temps[0]
            self.delta_temps = np.array([temp - first_temp for temp in self.temps])

            headers = df.columns.values.tolist()
            wave_headers = [head for head in headers if "Wave" in head]
            pow_headers = [head for head in headers if "Pow" in head]
            for wave_head, pow_head in zip(wave_headers, pow_headers):
                self.wavelengths.append(df[wave_head])
                self.powers.append(df[pow_head])

            self.delta_wavelengths_pm = np.array([np.array([(w - wave[0]) * 1000 for w in wave])
                                                  for wave in self.wavelengths])
            self.delta_powers = np.array([np.array([p - power[0] for p in power]) for power in self.powers])
            self.mean_delta_wavelengths_pm = np.array(self.delta_wavelengths_pm[0])
            self.mean_delta_powers = np.array(self.delta_powers[0])

            for wave_diff, pow_diff in zip(self.delta_wavelengths_pm[1:], self.delta_powers[1:]):
                self.mean_delta_wavelengths_pm += wave_diff
                self.mean_delta_powers += pow_diff
            self.mean_delta_wavelengths_pm /= len(fbg_names)
            self.mean_delta_powers /= len(fbg_names)

            self.delta_temps = list(self.delta_temps)
            self.delta_wavelengths_pm = list(self.delta_wavelengths_pm)
            self.delta_powers = list(self.delta_powers)
            self.mean_delta_wavelengths_pm = list(self.mean_delta_wavelengths_pm)
            self.mean_delta_powers = list(self.mean_delta_powers)
            if is_cal:
                self.drift_rates = list(df['Drift Rate'])
        except (KeyError, IndexError) as e:
            if main_queue is not None:
                main_queue.put(Message(MessageType.DEVELOPER, "File Helper Create Data Coll Error Dump", str(e)))
            raise RuntimeError("No data has been collected yet")
