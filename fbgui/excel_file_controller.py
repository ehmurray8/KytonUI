import queue
from tkinter import messagebox
from typing import Tuple

import pandas as pd
from StyleFrame import Styler, utils, StyleFrame
from openpyxl.chart import ScatterChart, Reference, Series, marker
from openpyxl.chart.shapes import GraphicalProperties
from openpyxl.drawing.colors import ColorChoice, RGBPercent
from openpyxl.worksheet import Worksheet

from fbgui.calibration_excel_container import CalibrationExcelContainer
from fbgui.constants import CAL, HEX_COLORS
from fbgui.data_container import DataCollection
from fbgui.database_controller import DatabaseController
from fbgui.helpers import get_file_name
from fbgui.messages import *

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


class ExcelFileController:
    def __init__(self, excel_file_path: str, fbg_names: List[str], main_queue: queue.Queue, function_type: str):
        self.excel_file_path = excel_file_path
        self.excel_file_name = get_file_name(excel_file_path)
        self.fbg_names = fbg_names
        self.main_queue = main_queue
        self.database_controller = DatabaseController(excel_file_path, fbg_names, main_queue, function_type)
        self.is_calibration = function_type == CAL

    def create_excel(self):
        try:
            if self.is_calibration:
                self.create_calibration_excel()
            else:
                self.create_baking_excel()
        except (RuntimeError, IndexError):
            self.main_queue.put(Message(MessageType.WARNING, "Excel File Creation Error",
                                        "No data has been recorded yet, or the database has been corrupted."))
        except PermissionError:
            message = "Please close {}, before attempting to create a new copy of it.".format(self.excel_file_name)
            self.main_queue.put(Message(MessageType.WARNING, "Excel File Creation Error", message))
            messagebox.showwarning("Excel file is already opened", message)

    def create_baking_excel(self):
        data_frame = self.database_controller.to_data_frame()
        data_collection = DataCollection()
        data_collection.create(self.is_calibration, data_frame, self.fbg_names, self.main_queue)
        column_ordering = [DATE_TIME_HEADER, DELTA_TIME_HEADER, TEMPERATURE_HEADER]

        add_times(data_frame, data_collection)
        add_wavelength_power_columns(column_ordering, data_frame)

        add_baking_duplicate_columns(data_frame, data_collection)
        column_ordering.extend([DELTA_TIME_HEADER1, DELTA_TEMPERATURE_HEADER1])
        self.add_delta_wavelengths(data_frame, data_collection, column_ordering)
        column_ordering.extend([DELTA_TIME_HEADER2, DELTA_TEMPERATURE_HEADER2])
        self.add_delta_powers(data_frame, data_collection, column_ordering)

        column_ordering.extend([DELTA_TEMPERATURE_HEADER3, MEAN_DELTA_WAVELENGTH_HEADER, MEAN_DELTA_POWER_HEADER])
        data_frame[MEAN_DELTA_WAVELENGTH_HEADER] = data_collection.mean_delta_wavelengths_pm
        data_frame[MEAN_DELTA_POWER_HEADER] = data_collection.mean_delta_powers
        data_frame = data_frame[column_ordering]

        style_frame = self.create_style_frame(data_frame)
        style_frame.apply_column_style(cols_to_style=MEAN_DELTA_WAVELENGTH_HEADER,
                                       styler_obj=Styler(font_color=utils.colors.red))
        style_frame.apply_column_style(cols_to_style=[DATE_TIME_HEADER],
                                       styler_obj=Styler(number_format=utils.number_formats.date_time_with_seconds))
        delta_temperature_headers = [col for col in data_frame.columns.values if DELTA_TEMPERATURE_HEADER in col]
        style_frame.apply_column_style(cols_to_style=delta_temperature_headers,
                                       styler_obj=Styler(font_color=utils.colors.red))
        self.show_excel([style_frame], ["Baking Data"], len(data_frame.index))

    def create_calibration_excel(self):
        data_frame = self.database_controller.to_data_frame()
        data_collection = DataCollection()
        data_collection.create(self.is_calibration, data_frame, self.fbg_names, self.main_queue)

        real_point_data_frame = data_frame[data_frame[REAL_POINT_HEADER] == "True"]
        cycles = list(set(real_point_data_frame[CYCLE_HEADER]))
        cycles.sort()
        del real_point_data_frame[REAL_POINT_HEADER]
        del real_point_data_frame[DATE_TIME_HEADER]
        del data_frame[REAL_POINT_HEADER]
        del data_frame[CYCLE_HEADER]

        full_column_ordering = [DATE_TIME_HEADER, DELTA_TIME_HEADER, TEMPERATURE_HEADER]

        add_times(data_frame, data_collection)
        add_wavelength_power_columns(full_column_ordering, data_frame)
        data_frame = data_frame[full_column_ordering]

        container = CalibrationExcelContainer(real_point_data_frame, cycles)
        calibration_data_frame = container.get_data_frame()
        calibration_style_frame = self.create_style_frame(calibration_data_frame)
        full_style_frame = self.create_style_frame(data_frame)
        delta_temperature_headers = [col for col in data_frame.columns.values if DELTA_TEMPERATURE_HEADER in col]
        full_style_frame.apply_column_style(cols_to_style=delta_temperature_headers,
                                            styler_obj=Styler(font_color=utils.colors.red))
        self.show_excel([calibration_style_frame, full_style_frame], ["Cal", "Full Cal"],
                        len(calibration_data_frame.index), container.deviation_indexes, container.cycles)

    def add_delta_wavelengths(self, data_frame: pd.DataFrame, data_collection: DataCollection,
                              column_ordering: List[str]):
        delta_wavelengths = data_collection.delta_wavelengths_pm
        for fbg_name, delta_wave in zip(self.fbg_names, delta_wavelengths):
            delta_wavelength_header = "{} {}{} (pm.)".format(fbg_name, u"\u0394", u"\u03BB")
            data_frame[delta_wavelength_header] = delta_wave
            column_ordering.append(delta_wavelength_header)

    def add_delta_powers(self, data_frame: pd.DataFrame, data_collection: DataCollection, column_ordering: List[str]):
        delta_powers = data_collection.delta_powers
        for fbg_name, delta_power in zip(self.fbg_names, delta_powers):
            delta_power_header = "{} {}{} (dBm.)".format(fbg_name, u"\u0394", "P")
            data_frame[delta_power_header] = delta_power
            column_ordering.append(delta_power_header)

    def create_style_frame(self, data_frame: pd.DataFrame):
        defaults = {'font_size': 14}
        style_frame = StyleFrame(data_frame, styler_obj=Styler(**defaults, shrink_to_fit=False, wrap_text=False))

        header_style = Styler(bold=True, font_size=18)
        style_frame.set_column_width(columns=style_frame.columns, width=35)
        style_frame.apply_headers_style(styler_obj=header_style)

        for fbg_name, hex_color in zip(self.fbg_names, HEX_COLORS):
            style_frame.apply_column_style(cols_to_style=[col for col in data_frame.columns.values if fbg_name in col],
                                           styler_obj=Styler(bg_color=hex_color))
        temperature_headers = [col for col in data_frame.columns.values if "Temperature" in col]
        style_frame.apply_column_style(cols_to_style=temperature_headers,
                                       styler_obj=Styler(font_color=utils.colors.red))
        return style_frame

    def show_excel(self, style_frames: List[StyleFrame], sheet_names: List[str], num_rows: int,
                   deviation_indexes=None, cycles: List[int]=None):
        ew = StyleFrame.ExcelWriter(self.excel_file_path)
        for style_frame, sheet_name in zip(style_frames, sheet_names):
            style_frame.to_excel(excel_writer=ew, row_to_add_filters=0, sheet_name=sheet_name)

        chart_sheet = ew.book.create_sheet(title="Chart")
        if self.is_calibration:
            self.graph_calibration(chart_sheet, ew.sheets[sheet_names[0]], num_rows, deviation_indexes, cycles)
        else:
            self.graph_bake(chart_sheet, ew.sheets[sheet_names[0]], num_rows)

        ew.save()
        ew.close()
        os.startfile('"{}"'.format(self.excel_file_path.replace("\\", "\\\\")))

    def graph_bake(self, chart_sheet: Worksheet, baking_sheet: Worksheet, num_rows: int):
        chart = ScatterChart()
        chart.height = 15
        chart.width = 30

        last_row = num_rows + 1
        x_values = Reference(baking_sheet, min_col=2, min_row=2, max_row=last_row)
        for i, fbg_name in enumerate(self.fbg_names):
            y_values = Reference(baking_sheet, min_col=4 + i, min_row=2, max_row=last_row)
            series = self.create_series_bake(x_values, y_values, i)
            chart.series.append(series)

        chart.title = "{} Time vs. Wavelength (nm.)".format(u"\u0394")
        chart.x_axis.title = "{} Time (hr.)".format(u"\u0394")
        chart.y_axis.title = "Wavelength (nm.)"
        chart_sheet.add_chart(chart, "B2")

    def graph_calibration(self, chart_sheet: Worksheet, calibration_sheet: Worksheet, num_rows: int,
                          deviation_indexes: List[int], cycles: List[int]):
        last_row = num_rows + 1
        min_col_x = 1
        start_row = 2
        deviation_index = 0
        for i, fbg_name in enumerate(self.fbg_names):
            chart = ScatterChart()
            chart.height = 15
            chart.width = 30
            chart.x_axis.scaling.min = 310
            chart.x_axis.scaling.max = 400
            if i != 0:
                min_col_x += i * (len(self.fbg_names) * 2 + 1)
            for cycle in cycles:
                x_values = Reference(calibration_sheet, min_col=min_col_x, min_row=2, max_row=last_row)
                y_values = Reference(calibration_sheet, min_col=deviation_indexes[deviation_index] + 1,
                                     min_row=2, max_row=last_row)
                series = Series(xvalues=x_values, values=y_values, title="Cycle {}".format(cycle))
                series.marker = marker.Marker("dot")
                series.graphicalProperties.line.noFill = True
                chart.series.append(series)
                deviation_index += 1
            chart.title = "{} Temperature vs. Wavelength Deviation".format(self.fbg_names[i])
            chart.x_axis.title = "Temperature (K)"
            chart.y_axis.title = "Wavelength Deviation from Mean (nm.)"
            chart_sheet.add_chart(chart, "B" + str(start_row + (i * 30)))

    def create_series_bake(self, x_values: Reference, y_values: Reference, index: int) -> Series:
        series = Series(values=y_values, xvalues=x_values, title=self.fbg_names[index])
        rgb_percent = RGBPercent(*hex_to_rgb(index))
        series.marker = marker.Marker(symbol="dot", spPr=GraphicalProperties(solidFill=ColorChoice(rgb_percent)))
        series.graphicalProperties.line.noFill = True
        return series


def add_times(data_frame: pd.DataFrame, data_collection: DataCollection):
    data_frame[DATE_TIME_HEADER] = data_frame[DATE_TIME_HEADER] \
        .apply(lambda x: x.tz_localize("UTC").tz_convert("US/Eastern"))
    data_frame[DELTA_TIME_HEADER] = data_collection.times


def add_wavelength_power_columns(column_ordering: List[str], data_frame: pd.DataFrame):
    wavelength_headers, power_headers = get_wavelength_power_headers(data_frame)
    column_ordering.extend(wavelength_headers)
    column_ordering.extend(power_headers)


def add_baking_duplicate_columns(data_frame: pd.DataFrame, data_collection: DataCollection):
    data_frame[DELTA_TIME_HEADER1] = data_frame[DELTA_TIME_HEADER]
    data_frame[DELTA_TIME_HEADER2] = data_frame[DELTA_TIME_HEADER]
    data_frame[DELTA_TEMPERATURE_HEADER] = data_collection.delta_temps
    data_frame[DELTA_TEMPERATURE_HEADER1] = data_collection.delta_temps
    data_frame[DELTA_TEMPERATURE_HEADER2] = data_collection.delta_temps
    data_frame[DELTA_TEMPERATURE_HEADER3] = data_collection.delta_temps


def get_wavelength_power_headers(data_frame: pd.DataFrame) -> Tuple[List[str], List[str]]:
    headers = data_frame.columns.values.tolist()
    wavelength_headers = [head for head in headers if "Wave" in head]
    power_headers = [head for head in headers if "Pow" in head]
    return wavelength_headers, power_headers


def hex_to_rgb(hex_index: int) -> List[float]:
    hex_string = HEX_COLORS[hex_index][1:]
    rgb_list = []  # type: List[float]
    for i in range(0, len(hex_string), 2):
        hex_int = int(hex_string[i:i+2], 16) / 255 * 100
        rgb_list.append(hex_int)
    return rgb_list

