import enum
from typing import Optional, List

from openpyxl.worksheet import Worksheet

from fbgui.constants import *


class CalibrationGraphType(enum.Enum):
    DEVIATION = ("{} deviation from mean ({})", "Cycle {}", "B")
    MEAN = ("{} mean ({})", "Mean", "V")
    SENSITIVITY = ("{} sensitivity ({}/K)", "Sensitivity", "AP")

    def __init__(self, y_axis_specifier, series_title, column_letter):
        self.y_axis_specifier = y_axis_specifier
        self.series_title = series_title
        self.column_letter = column_letter


class CalibrationReadingType(enum.Enum):
    WAVELENGTH = ("Wavelength", "pm")
    POWER = ("Power", "db")

    def __init__(self, title: str, units: str):
        self.title = title
        self.units = units


class CalibrationGraphSubType(enum.Enum):
    WAVELENGTH_DEVIATION = (CalibrationGraphType.DEVIATION, CALIBRATION_GRAPH_START_ROW,
                            CalibrationReadingType.WAVELENGTH)
    WAVELENGTH_MEAN = (CalibrationGraphType.MEAN, CALIBRATION_GRAPH_START_ROW,
                       CalibrationReadingType.WAVELENGTH, "nm")
    WAVELENGTH_SENSITIVITY = (CalibrationGraphType.SENSITIVITY, CALIBRATION_GRAPH_START_ROW,
                              CalibrationReadingType.WAVELENGTH)
    POWER_DEVIATION = (CalibrationGraphType.DEVIATION, None, CalibrationReadingType.POWER)
    POWER_MEAN = (CalibrationGraphType.MEAN, None, CalibrationReadingType.POWER)
    POWER_SENSITIVITY = (CalibrationGraphType.SENSITIVITY, None, CalibrationReadingType.POWER)

    def __init__(self, graph_type: CalibrationGraphType, start_row: Optional[int],
                 reading_type: CalibrationReadingType, mean_units: str=None):
        self._graph_type = graph_type
        self._start_row = start_row
        self._reading_type = reading_type
        self._mean_units = mean_units

    def get_start_row(self, num_fbgs: int) -> int:
        return self._start_row if self._start_row is not None else CALIBRATION_GRAPH_START_ROW + num_fbgs * 30

    def get_column_letter(self):
        return self._graph_type.column_letter

    def get_series_title(self, num: int) -> str:
        return self._graph_type.series_title.format(num)

    def y_axis_title(self):
        units = self._reading_type.units if self._mean_units is None else self._mean_units
        return self._graph_type.y_axis_specifier.format(self._reading_type.title, units)


class GraphParameters:

    def __init__(self, num_rows: int):
        self.chart_sheet = None  # type: Worksheet
        self.data_sheet = None  # type: Worksheet
        self.num_rows = num_rows


class BakingGraphParameters(GraphParameters):

    def __init__(self, num_rows: int, trend_line_indexes: List[int]):
        super().__init__(num_rows)
        self.trend_line_indexes = trend_line_indexes


class CalibrationGraphParameters(GraphParameters):

    def __init__(self, num_rows: int, temperatures: List[float], cycles: List[int],
                 mean_wavelength_indexes: List[int], deviation_wavelength_indexes: List[int],
                 mean_power_indexes: List[int], deviation_power_indexes: List[int],
                 sensitivity_wavelength_indexes: List[int], sensitivity_power_indexes: List[int],
                 master_temperature_column: int=0, mean_temperature_column: int=0):
        super().__init__(num_rows)
        self.temperatures = temperatures
        self.mean_wavelength_indexes = mean_wavelength_indexes
        self.deviation_wavelength_indexes = deviation_wavelength_indexes
        self.mean_power_indexes = mean_power_indexes
        self.deviation_power_indexes = deviation_power_indexes
        self.sensitivity_wavelength_indexes = sensitivity_wavelength_indexes
        self.sensitivity_power_indexes = sensitivity_power_indexes
        self.master_temperature_column = master_temperature_column
        self.mean_temperature_column = mean_temperature_column
        self.cycles = cycles


class SeriesParameters:
    def __init__(self, parameters: CalibrationGraphParameters, indexes: List[int], sub_type: CalibrationGraphSubType):
        self.indexes = indexes
        self.data_sheet = parameters.data_sheet
        self.last_row = parameters.num_rows + 1
        self.sub_type = sub_type
        self.cycles = parameters.cycles
