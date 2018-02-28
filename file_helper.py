"""Module used for helping with creating output files."""

import os
import numpy as np
import datetime
from StyleFrame import Styler, utils, StyleFrame
import sqlite3
from tkinter import messagebox as mbox
import pandas as pd
import data_container as datac
import helpers as help
from constants import HEX_COLORS, CAL, BAKING


def write_db(file_name, serial_nums, timestamp, temp, wavelengths, powers,
             func, table, drift_rate=None, real_cal_pt=False):
    """Writes the output to sqlite database."""
    conn = sqlite3.connect("db/program_data.db")
    cur = conn.cursor()
    name = help.get_file_name(file_name)
    prog_exists = program_exists(name, cur, func)

    wave_pow = []
    for wave, power in zip(wavelengths, powers):
        wave_pow.append(wave)
        wave_pow.append(power)
    col_list = create_headers_init(serial_nums, func == CAL)
    cols = ",".join(col_list)
    if not prog_exists:
        try:
            cur.execute("INSERT INTO map('ProgName', 'ProgType') VALUES ('{}', '{}')".format(name, func.lower()))
        except sqlite3.OperationalError:
            cur.execute("CREATE TABLE 'map' ( 'ID' INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,"
                        "'ProgName' TEXT NOT NULL, 'ProgType' INTEGER NOT NULL")
            cur.execute("INSERT INTO map('ProgName', 'ProgType') VALUES ('{}', '{}')".format(name, func.lower()))
        cur.execute("SELECT ID FROM map WHERE ProgName = '{}';".format(name))
        table_id = cur.fetchall()[0][0]
        cur.execute("CREATE TABLE `{}` ({});".format(func.lower() + str(table_id), cols))

    readable_time = datetime.datetime.fromtimestamp(int(timestamp)).strftime("%d/%m/%y %H:%M")
    values_list = [readable_time, *wave_pow, temp]
    if func == CAL:
        values_list.append(drift_rate)
        values_list.append(real_cal_pt)
    headers = create_headers(serial_nums, func == CAL, False)
    headers_f = create_headers(serial_nums, func == CAL, True)
    headers_f.pop(0)
    headers.pop(0)
    table.setup_headers(headers_f)
    table.add_data(values_list)
    cur.execute("SELECT ID FROM map WHERE ProgName = '{}';".format(name))
    table_id = cur.fetchall()[0][0]
    values_list[0] = timestamp
    values = ",".join([str(val) for val in values_list])
    cur.execute("INSERT INTO {}({}) VALUES ({})".format(func.lower() + str(table_id), ",".join(headers), values))
    conn.commit()
    conn.close()


def program_exists(name, cur_map, func):
    cur_map.execute("SELECT ID, ProgName, ProgType from map")
    rows = cur_map.fetchall()
    names = [row[1] for row in rows]
    types = [row[2] for row in rows]
    prog_exists = False
    try:
        idx = names.index(name)
        if types[idx] == func.lower():
            prog_exists = True
    except ValueError:
        pass
    return prog_exists


def create_headers(snums, is_cal, formatted):
    snum_cols = []
    for snum in snums:
        snum_cols.append("'{} Wavelength (nm.)'".format(snum))
        snum_cols.append("'{} Power (dBm.)'".format(snum))
    col_list = ["ID", "'Date Time'", *snum_cols, "'Mean Temperature (K)'"]
    if is_cal:
        col_list.append("'Drift Rate'")
        col_list.append("'Real Point'")
    if formatted:
        col_list = [s.replace("'", "") for s in col_list]
    return col_list


def create_headers_init(snums, is_cal):
    snum_cols = []
    for snum in snums:
        snum_cols.append("'{} Wavelength (nm.)' REAl NOT NULL".format(snum))
        snum_cols.append("'{} Power (dBm.)' REAL NOT NULL".format(snum))
    col_list = ["ID INTEGER NOT NULL PRIMARY KEY", "'Date Time' REAL NOT NULL",
                *snum_cols, "'Mean Temperature (K)' REAL NOT NULL"]
    if is_cal:
        col_list.append("'Drift Rate' REAL NOT NULL")
        col_list.append("'Real Point' INTEGER NOT NULL")
    return col_list


async def add_table_data(table, name, is_cal, snums):
    table.reset()
    conn = sqlite3.connect("db/program_data.db")
    cur = conn.cursor()

    headers_f = create_headers(snums, is_cal, True)
    headers_f.pop(0)
    table.setup_headers(headers_f)
    cur.execute("SELECT ID FROM map WHERE ProgName = '{}';".format(name))
    func = BAKING
    if is_cal:
        func = CAL
    table_id = cur.fetchall()[0][0]
    df = pd.read_sql_query("SELECT * from {}".format(func.lower() + str(table_id)), conn)
    del df["ID"]
    conn.close()
    table.add_data(df)


def db_to_df(func, name):
    try:
        conn = sqlite3.connect("db/program_data.db")
        cur = conn.cursor()
        cur.execute("SELECT {} from {} WHERE ProgName = '{}'".format("ID", "map", name))
        table_id = cur.fetchall()[0][0]
        df = pd.read_sql_query("SELECT * from {}".format(func.lower() + str(table_id)), conn)
        del df["ID"]
        conn.close()
        return df
    except (pd.io.sql.DatabaseError, sqlite3.OperationalError):
        return pd.DataFrame()


def create_data_coll(name, snums, is_cal):
    try:
        func = BAKING
        if is_cal:
            func = CAL
        df = db_to_df(func, name)
        data_coll = datac.DataCollection()
        headers = create_headers(snums, is_cal, True)
        data_coll.timestamps = df["Date Time"]
        start_time = df["Date Time"][0]
        df['Date Time'] = pd.to_datetime(df['Date Time'], unit="s")
        data_coll.times = [(time - start_time) / 60 / 60 for time in data_coll.timestamps]
        data_coll.temps = df["Mean Temperature (K)"]
        first_temp = data_coll.temps[0]
        data_coll.temp_diffs = np.array([temp - first_temp for temp in data_coll.temps])
        wave_headers = [head for head in headers if "Wave" in head]
        pow_headers = [head for head in headers if "Pow" in head]
        for wave_head, pow_head in zip(wave_headers, pow_headers):
            data_coll.wavelens.append(df[wave_head])
            data_coll.powers.append(df[pow_head])
        data_coll.wavelen_diffs = np.array([np.array([w - wave[0] for w in wave]) for wave in data_coll.wavelens])
        data_coll.power_diffs = np.array([np.array([p - power[0] for p in power]) for power in data_coll.powers])
        data_coll.mean_wavelen_diffs = np.array(data_coll.wavelen_diffs[0])
        data_coll.mean_power_diffs = np.array(data_coll.power_diffs[0])
        for wave_diff, pow_diff in zip(data_coll.wavelen_diffs[1:], data_coll.power_diffs[1:]):
            data_coll.mean_wavelen_diffs += wave_diff
            data_coll.mean_power_diffs += pow_diff
        data_coll.mean_wavelen_diffs /= len(data_coll.mean_wavelen_diffs)
        data_coll.mean_wavelen_diffs *= 1000
        data_coll.mean_power_diffs /= len(data_coll.mean_power_diffs)
        return data_coll, df
    except (KeyError, IndexError):
        raise RuntimeError("No data has been collected yet")


def create_excel_file(xcel_file, snums, is_cal=False):
    """Creates an excel file from the correspoding csv file."""
    try:
        data_coll, df = create_data_coll(help.get_file_name(xcel_file), snums, is_cal)
        new_df = pd.DataFrame()
        new_df["Date Time"] = df["Date Time"]
        new_df["{} Time (hr.)".format(u"\u0394")] = data_coll.times
        del df["Date Time"]
        for col in df.columns.values.tolist():
            new_df[col] = df[col]
        new_df.append(df)
        new_df["Date Time"] = new_df["Date Time"].apply(lambda x: x.tz_localize("UTC").tz_convert("US/Eastern"))
        for snum, delta_wave in zip(snums, data_coll.wavelen_diffs):
            new_df["{} {}{}, from start (nm).".format(snum, u"\u0394", u"\u03BB")] = delta_wave

        new_df["{}T, from start (K)".format(u"\u0394")] = data_coll.temp_diffs
        new_df["Mean raw {}{}, from start (pm.)".format(u"\u0394", u"\u03BB")] = data_coll.mean_wavelen_diffs

        defaults = {'font_size': 14}
        sf = StyleFrame(new_df, styler_obj=Styler(**defaults, shrink_to_fit=False, wrap_text=False))

        # Style the headers of the table
        header_style = Styler(bold=True, font_size=18)
        sf.set_column_width(columns=sf.columns, width=35)
        sf.apply_headers_style(styler_obj=header_style)

        sf.apply_column_style(cols_to_style='Date Time',
                              styler_obj=Styler(number_format=utils.number_formats.date_time_with_seconds))

        wave_heads = [col for col in new_df.columns.values if "Wave" in col]
        pow_heads = [col for col in new_df.columns.values if "Pow" in col]
        for wave_head, pow_head, hex_color in zip(wave_heads, pow_heads, HEX_COLORS):
            sf.apply_column_style(cols_to_style=[wave_head, pow_head],
                                  styler_obj=Styler(bg_color=hex_color))
        sf.apply_column_style(cols_to_style="Mean Temperature (K)", styler_obj=Styler(font_color=utils.colors.red))
        sf.apply_column_style(cols_to_style="{}T, from start (K)".format(u"\u0394"),
                              styler_obj=Styler(font_color=utils.colors.red))
        sf.apply_column_style(cols_to_style="Mean raw {}{}, from start (pm.)".format(u"\u0394", u"\u03BB"),
                              styler_obj=Styler(font_color=utils.colors.red))

        ew = StyleFrame.ExcelWriter(xcel_file)
        sf.to_excel(excel_writer=ew, row_to_add_filters=0, sheet_name="Sheet1")
        ew.save()
        # Freeze the columns before column 'A' (=None) and rows above '2' (=1).
        # columns_and_rows_to_freeze='A2').save()
        os.startfile('"{}"'.format(xcel_file.replace("\\", "\\\\")))
    except RuntimeError:
        mbox.showwarning("Error creating Excel File",
                         "No data has been recorded yet, or the database has been corrupted.")
