"""Module used for helping with creating output files."""
# pylint: disable=import-error, relative-import
# pylint: disable-msg=too-many-arguments, too-many-branches, too-many-locals

import os
import asyncio
import time
from datetime import datetime
import numpy as np
import openpyxl
import pyodbc
import getpass
from tkinter import messagebox
import xlsxwriter
import pandas as pd
import data_container as datac
import helpers as help
from constants import HEX_COLORS, CAL, BAKING


def write_db(file_name, serial_nums, timestamp, temp, wavelengths, powers,
             func, table, drift_rate=None, real_cal_pt=False):
    """Writes the output csv file."""

    conn_map = connect_db("bakecalmap")
    cur_map = conn_map.cursor()

    name = help.get_file_name(file_name)
    prog_exists, last_id = program_exists(name, cur_map, func)

    conn_prog = connect_db(func.lower())
    cur_prog = conn_prog.cursor()
    wave_pow = []
    for wave, power in zip(wavelengths, powers):
        wave_pow.append(wave)
        wave_pow.append(power)
    col_list = create_headers(serial_nums, func == CAL)
    cols = ",".join(col_list)
    if not prog_exists:
        cur_map.execute("INSERT INTO map VALUES ({}, {}, {})".format(last_id+1, "'{}'".format(name),
                                                                     "'{}'".format(func.lower())))
        conn_map.commit()
        table.setup_headers(col_list)
        cur_prog.execute("CREATE TABLE {} ({});".format(name, cols))
        last_id = 0
        delta_time = 0
    else:
        cur_prog.execute("SELECT ID from {}".format(name))
        rows = cur_prog.fetchall()
        last_id = rows[-1][0] + 1
        first_timestamp = rows[0][1]
        delta_time = timestamp - first_timestamp
    conn_map.close()
    values_list = [last_id, timestamp, delta_time, *wave_pow, temp]
    if func == CAL:
        values_list.append(drift_rate)
        values_list.append(real_cal_pt)
    values = ",".join(values_list)
    table.add_data(values_list)
    cur_prog.execute("INSERT INTO {} VALUES ({})".format(name, values))
    conn_prog.commit()
    conn_prog.close()


def connect_db(name):
    username = getpass.getuser()
    conn_str = r'DRIVER={Microsoft Access Driver (*.mdb, *.accdb)};DBQ=C:\Users\\' + username
    conn_str += r'\AppData\Local\Databases\\' + name + ".accdb"
    return pyodbc.connect(conn_str)


def program_exists(name, cur_map, func):
    cur_map.execute("SELECT ID, ProgName, ProgType from map")
    rows = cur_map.fetchall()
    try:
        last_id = [row[0] for row in rows][-1][0]
    except IndexError:
        last_id = 0
    names = [row[1] for row in rows]
    types = [row[2] for row in rows]
    prog_exists = False
    try:
        idx = names.index(name)
        if types[idx] == func.lower():
            prog_exists = True
    except ValueError:
        pass
    return prog_exists, last_id


def create_headers(snums, is_cal):
    snum_cols = []
    for snum in snums:
        snum_cols.append("'{}_Wave DOUBLE NOT NULL".format(snum))
        snum_cols.append("'{}_Pow DOUBLE NOT NULL".format(snum))
    col_list = ["ID INT PRIMARY KEY NOT NULL", "ReadingTime DOUBLE NOT NULL",
                "Delta_Time DOUBLE NOT NULL",
                *snum_cols, "Temperature DOUBLE NOT NULL"]
    if is_cal:
        col_list.append("DriftRate DOUBLE NOT NULL")
        col_list.append("RealPoint BOOL NOT NULL")
    return col_list


def update_table(table, xcel_file, is_cal, new_loop, mutex, snums):
    func = BAKING
    if is_cal:
        func = CAL
    conn = connect_db("bakecalmap")
    cur = conn.cursor()
    name = os.path.splitext(os.path.split(xcel_file)[1])[0]
    if program_exists(name, cur, func)[0]:
        conn.close()
        asyncio.set_event_loop(new_loop)
        new_loop.run_until_complete(add_table_data(table, name, is_cal, mutex, snums))
    else:
        conn.close()
    new_loop.close()
    #if table.stop_flag:
    #    table.stop_flag = False
    #    #mutex.release()


async def add_table_data(table, name, is_cal, mutex, snums):
    table.reset()
    headers = create_headers(snums, is_cal)
    table.setup_headers(headers)
    db = BAKING.lower()
    if is_cal:
        db = CAL.lower()
    conn = connect_db(db)
    cur = conn.cursor()
    headers_str = ",".join(headers)
    cur.execute("SELECT {} from {}".format(headers_str, name))
    rows = cur.fetchall()
    conn.close()
    for row in rows:
        table.add_data(row)
        #if table.stop_flag:
        #    table.reset()
        #    table.setup_headers(headers)
        #    table.stop_flag = False
        #    mutex.release()
        #    break


def db_to_df(name, snums, is_cal):
    conn = connect_db(name)
    cur = conn.cursor()
    cur.execute("SELECT * from {}".format(name))
    rows = cur.fetchall()
    conn.close()

    headers = [""]
    return pd.DataFrame(data={h: d for h, d in zip(headers, rows)})


def create_data_coll(name, snums, is_cal):
    data_coll = datac.DataCollection()
    df, headers = db_to_df(name, snums, is_cal)
    data_coll.timestamps = df["ReadingTime"]
    data_coll.times = df["DeltaTime"]
    data_coll.temps = df["Temperature"]
    first_temp = data_coll.temps[0]
    data_coll.temp_diffs = np.array([temp - first_temp for temp in data_coll.temps])
    wave_headers = [head for head in headers if "Wave" in head]
    pow_headers = [head for head in headers if "Pow" in head]
    for wave_head, pow_head in zip(wave_headers, pow_headers):
        data_coll.wavelens.append(df[wave_head])
        data_coll.powers.append(df[pow_head])
    data_coll.wavelen_diffs = np.array([np.array(w - data_coll.wavelens[0]) for w in data_coll.wavelens])
    data_coll.power_diffs = np.array([np.array(p - data_coll.powers[0] for p in data_coll.powers)])
    data_coll.mean_wavelen_diffs = sum(data_coll.wavelen_diffs) / len(data_coll.wavelen_diffs)
    data_coll.mean_power_diffs = sum(data_coll.power_diffs) / len(data_coll.power_diffs)
    return data_coll


def create_excel_file(xcel_file, snums, is_cal=False):
    """Creates an excel file from the correspoding csv file."""

    wb = openpyxl.Workbook()
    ws = wb.active

    df = db_to_df(help.get_file_name(xcel_file), snums, is_cal)
    for r in openpyxl.utils.dataframe.dataframe_to_rows(df, index=True, header=True):
        ws.append(r)

    for cell in ws['A'] + ws[1]:
        cell.style = 'Pandas'

    wb.save(xcel_file)
    # csv_file = help.to_ext(xcel_file, "csv")
    # if os.path.isfile(csv_file):
    #    mdata, entries_df = parse_csv_file(csv_file)
    #    if entries_df is not None:
    #        num_cols = len(mdata.serial_nums) * 3 + 5

    #        workbook = xlsxwriter.Workbook(xcel_file)
    #        worksheet = workbook.add_worksheet()
    #        headers = __create_headers(mdata.serial_nums, worksheet, num_cols, is_cal)
    #        row_strs, data_coll = __create_row_strs(mdata, entries_df, is_cal)

    #        bf = workbook.add_format({"bold": True, "font_size": 16})
    #        bf.set_bold()
    #        row_format, row_header_format = __create_formats(mdata.serial_nums, workbook, bf, is_cal)

    #        __write_headers(headers, row_header_format, bf, worksheet)
    #        __write_rows(row_strs, row_format, worksheet, bf, data_coll, is_cal)
    #        worksheet.set_column(0, num_cols, 37)
    #        col_end = __create_chart(entries_df, mdata.serial_nums, num_cols, worksheet, workbook)
    #        if is_cal:
    #            __create_chart_dr(data_coll, worksheet, workbook, col_end)

    #        workbook.close()
    #        os.system("start " + xcel_file)
    #    else:
    #        messagebox.showwarning("File Error",
    #                             "Error generating the excel file, please try to wait for more data to be collected." +
    #                               "If this error persists the csv data file may have been corrupted.")


def num_to_excel_col(num):
    """Converts num to excel col label, 1 indexed, only works with 1 or 2 letters"""
    letters = ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J', 'K', 'L', 'M', 'N', 'O'
               'P', 'Q', 'R', 'S', 'T', 'U', 'V', 'W', 'X', 'Y', 'Z']
    num -= 1
    curr_overflow_index = 0
    if num < 26:
        return letters[num]

    num -= 26
    while num >= 26:
        num -= 26
        curr_overflow_index += 1
    return letters[curr_overflow_index] + letters[num]




























































def __create_row_strs(mdata, entries_df, is_cal=False):
    data_coll = create_data_coll(mdata, entries_df, is_cal)

    row_num = 0
    row_strs = []
    for time_num, temp in zip(data_coll.times, data_coll.temps):
        row_strs.append([])
        row_strs[row_num].append(time.strftime("%a, %d %b %Y %H:%M:%S", time.localtime(time_num)))
        row_strs[row_num].append(round(time_num / 3600 - mdata.start_time / 3600, 5))

        idx = 0
        for wavelen, power in zip(data_coll.wavelens, data_coll.powers):
            row_strs[row_num].append(wavelen[row_num])
            row_strs[row_num].append(power[row_num])
            idx += 1

        row_strs[row_num].append(temp)

        for wave_diff in data_coll.wavelen_diffs:
            row_strs[row_num].append(wave_diff[row_num])

        row_strs[row_num].append(temp - mdata.start_temp)
        row_strs[row_num].append(data_coll.mean_wavelen_diffs[row_num])
        if is_cal:
            row_strs[row_num].append(data_coll.drift_rates[row_num])
        row_num += 1

    return row_strs, data_coll


def __create_formats(serial_nums, workbook, bold_format, is_cal=False):
    color_formats = []
    bold_color_formats = []
    for _, color in zip(serial_nums, HEX_COLORS):
        format_col = workbook.add_format({'bg_color': color})
        color_formats.append(format_col)
        bold_color_format = workbook.add_format({'bg_color': color, 'bold': True, 'font_size': 16})
        bold_color_formats.append(bold_color_format)

    std_head_f = workbook.add_format({'bold': True, 'font_size': 16})
    std_head_red_f = workbook.add_format({'bold': True, 'font_size': 16, 'font_color': 'red'})

    # Add time formats
    row_format = [None, None]
    row_header_format = [std_head_f, std_head_f]

    # Add color formats for wavelength and power data
    for color_f, b_color_f in zip(color_formats, bold_color_formats):
        row_format.append(color_f)
        row_format.append(color_f)
        row_header_format.append(b_color_f)
        row_header_format.append(b_color_f)

    format_red = workbook.add_format({'font_color': 'red'})

    # Add red text format for mean temperature
    row_format.append(format_red)
    row_header_format.append(std_head_red_f)

    # Add formats for delta wavelengths
    sn_num = 0
    while sn_num < len(serial_nums):
        row_format.append(None)
        row_header_format.append(bold_format)
        sn_num += 1

    # Add red text format for delta temperature, and format for mean delta wavelength
    row_format.append(format_red)
    row_format.append(None)
    row_header_format.append(std_head_red_f)
    row_header_format.append(std_head_red_f)
    # row_header_format.append(None)

    return row_format, row_header_format


def __write_headers(headers, row_header_format, bold_format, worksheet):
    col = 0
    for header, row_f in zip(headers, row_header_format):
        if row_f is None:
            worksheet.write(0, col, header, bold_format)
        else:
            worksheet.write(0, col, header, row_f)
        col += 1


def __write_rows(row_strs, row_format, worksheet, data_coll, bold_format, is_cal=False):
    row_num = 1
    for row in row_strs:
        col = 0
        for num, row_f in zip(row, row_format):
            try:
                num = float(num)
                num_str = "=VALUE({})".format(num)
            except ValueError:
                num_str = num

            if row_f is None:
                if is_cal and data_coll.real_points[row_num]:
                    worksheet.write(row_num, col, num_str, bold_format)
                else:
                    worksheet.write(row_num, col, num_str)
            else:
                if is_cal and data_coll.real_points[row_num]:
                    row_f.set_bold()
                    worksheet.write(row_num, col, num_str, row_f)
                else:
                    worksheet.write(row_num, col, num_str, row_f)
            col += 1
        row_num += 1


def __create_chart(entries, serial_nums, num_cols, worksheet, workbook):
    chart = workbook.add_chart({'type': 'scatter', 'subtype': 'smooth_with_markers'})
    cats = "=Sheet1!$B$2:$B$" + str(len(entries) + 1)
    val_col = num_to_excel_col((len(serial_nums) * 3) + 4)
    vals = "=Sheet1!$" + val_col + "$2:$" + val_col + "$" + str(len(entries) + 1)
    line_name = "Raw " + u'\u0394\u03BB' + "pm"
    chart.add_series({'name': line_name, 'categories': cats, 'values': vals})
    chart.set_title({'name': 'Baking: ' + u'\u0394\u03BB' + " (pm) vs. Time (hr) from start"})
    chart.set_y_axis({'name': u'\u0394\u03BB' + " average (pm)"})
    chart.set_x_axis({'name': 'Elapsed Time from start (hr)'})

    chart.set_style(10)
    col_name = num_to_excel_col(num_cols + 2)
    worksheet.insert_chart("${}$3".format(col_name), chart)
    return num_cols + 12


def __create_chart_dr(data_coll, worksheet, workbook, col_start):
    chart = workbook.add_chart({'type': 'scatter', 'subtype': 'smooth_with_markers'})
    times_real = []
    drates_real = []
    for time_num, drate in zip(data_coll.times, data_coll.drift_rates):
        times_real.append(time_num)
        drates_real.append(drate)

    chart.add_series({'name': 'Average Drift Rate (mK/min)', 'categories': times_real, 'values': drates_real})
    chart.set_title({'name': 'Average Drift Rate (mK/min) vs. Time(hr)'})
    chart.set_y_axis({'name': 'Average Drift Rate (mK/min)'})
    chart.set_x_axis({'name': 'Time (hr)'})

    chart.set_style(10)
    worksheet.insert_chart("${}$3".format(num_to_excel_col(col_start)), chart)


def check_metadata(file_lines, is_cal, num_fbgs=None):
    try:
        init_vals = help.list_cast(next(file_lines).split(","), float)
        if num_fbgs is not None and len(init_vals) != num_fbgs:
            return False
        config_vals = help.list_cast(next(file_lines).split(","), float)
        if len(config_vals) != 3:
            return False
        if next(file_lines) != "\n":
            return False
        headers = help.clean_str_list(next(file_lines).split(","))
        if not is_cal and headers != ["Serial Num", "Timestamp(s)", "Temperature(K)", "Wavelength(nm)", "Power(dBm)"]:
            return False
        elif is_cal and headers != ["Serial Num", "Timestamp(s)", "Temperature(K)", "Wavelength(nm)", "Power(dBm)",
                                    "Real Point", "Drift Rate(mK/min)"]:
            return False
        if next(file_lines) != "\n":
            return False
    except ValueError:
        return False

    return True
