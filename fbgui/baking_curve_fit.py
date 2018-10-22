import pandas as pd
import numpy.polynomial.polynomial as poly


def curve_fit_baking(data_frame: pd.DataFrame, x_index: int, y_index: int=1):
    x_column_name = data_frame.columns[x_index]
    x_values = data_frame[x_column_name]

    y_column_name = data_frame.columns[y_index]
    y_values = data_frame[y_column_name]

    return list(reversed(poly.polyfit(x_values, y_values, 1)))
