from typing import Iterable, List

import pandas as pd
import numpy.polynomial.polynomial as poly


def curve_fit_baking(data_frame: pd.DataFrame, y_index: int, x_index: int=1) -> List[float]:
    x_values = _get_values(data_frame, x_index)
    y_values = _get_values(data_frame, y_index)
    return list(reversed(poly.polyfit(x_values, y_values, 1)))


def add_baking_trend_line(data_frame: pd.DataFrame, coefficients: Iterable[float], fbg_name: str, x_index: int=1) -> int:
    x_values = _get_values(data_frame, x_index)
    y_values = poly.polyval(x_values, coefficients)
    column_name = "{} Trend Values".format(fbg_name)
    data_frame[column_name] = y_values
    return data_frame.columns.tolist().index(column_name)


def _get_values(data_frame: pd.DataFrame, index: int) -> Iterable[float]:
    column_name = data_frame.columns[index]
    return data_frame[column_name]