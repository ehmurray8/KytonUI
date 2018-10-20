import enum
from typing import Optional, List

from openpyxl.worksheet import Worksheet

from fbgui.constants import *


class CalibrationGraphType(enum.Enum):
    DEVIATION = ("Wavelength deviation from mean (pm)", "Cycle {}", "B")
    MEAN = ("Wavelength mean (nm)", "Mean", "V")

    def __init__(self, y_axis_specifier, series_title, column_letter):
        self.y_axis_specifier = y_axis_specifier
        self._series_title = series_title
        self.column_letter = column_letter

    def get_series_title(self, num: int) -> str:
        return self._series_title.format(num)


class CalibrationGraphSubType(enum.Enum):
    WAVELENGTH_DEVIATION = (CalibrationGraphType.DEVIATION, CALIBRATION_GRAPH_START_ROW)
    WAVELENGTH_MEAN = (CalibrationGraphType.MEAN, CALIBRATION_GRAPH_START_ROW)
    POWER_DEVIATION = (CalibrationGraphType.DEVIATION, None)
    POWER_MEAN = (CalibrationGraphType.MEAN, None)

    def __init__(self, graph_type: CalibrationGraphType, start_row: Optional[int]):
        self.graph_type = graph_type
        self._start_row = start_row

    def get_start_row(self, num_fbgs: int) -> int:
        return self._start_row if self._start_row is not None else CALIBRATION_GRAPH_START_ROW + num_fbgs * 30


class GraphParameters:

    def __init__(self, num_rows: int):
        self.chart_sheet = None  # type: Worksheet
        self.data_sheet = None  # type: Worksheet
        self.num_rows = num_rows


class CalibrationGraphParameters(GraphParameters):

    def __init__(self, num_rows: int, temperatures: List[float], cycles: List[int],
                 mean_wavelength_indexes: List[int], deviation_wavelength_indexes: List[int]):
        super().__init__(num_rows)
        self.temperatures = temperatures
        self.cycles = cycles
        self.mean_wavelength_indexes = mean_wavelength_indexes
        self.deviation_wavelength_indexes = deviation_wavelength_indexes


class SeriesParameters:
    def __init__(self, parameters: CalibrationGraphParameters, indexes: List[int], sub_type: CalibrationGraphSubType):
        self.indexes = indexes
        self.data_sheet = parameters.data_sheet
        self.last_row = parameters.num_rows + 1
        self.sub_type = sub_type
        self.cycles = parameters.cycles


