"""Module used for helping with creating output files."""
import datetime
import os
import sqlite3
from tkinter import messagebox as mbox
import data_container as datac
import numpy as np
import pandas as pd
from StyleFrame import Styler, utils, StyleFrame
from constants import HEX_COLORS, CAL, BAKING, DB_PATH, PROG_CONFIG_PATH
import helpers
import configparser


def write_db(file_name, serial_nums, timestamp, temp, wavelengths, powers,
             func, table, drift_rate=None, real_cal_pt=False):
    """Writes the output to sqlite database."""
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    name = helpers.get_file_name(file_name)
    prog_exists = program_exists(name, cur, func)

    wave_pow = []
    for wave, power in zip(wavelengths, powers):
        wave_pow.append(wave)
        wave_pow.append(power)
    col_list = create_headers_init(serial_nums, func == CAL)
    cols = ",".join(col_list)
    if not prog_exists:
        try:
            cur.execute("INSERT INTO map('ProgName', 'ProgType', 'FilePath', 'Snums') VALUES ('{}', '{}', '{}', '{}')"
                        .format(name, func.lower(), file_name, ",".join(serial_nums)))
        except sqlite3.OperationalError:
            cur.execute("CREATE TABLE 'map' ( 'ID' INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,"
                        "'ProgName' TEXT NOT NULL, 'ProgType' INTEGER NOT NULL, 'FilePath' TEXT, 'Snums' TEXT )")
            cur.execute("INSERT INTO map('ProgName', 'ProgType', 'FilePath', 'Snums') VALUES ('{}', '{}', '{}', '{}')"
                        .format(name, func.lower(), file_name, ",".join(serial_nums)))
        cur.execute("SELECT ID FROM map WHERE ProgName = '{}';".format(name))
        table_id = cur.fetchall()[0][0]
        cur.execute("CREATE TABLE `{}` ({});".format(func.lower() + str(table_id), cols))

    readable_time = datetime.datetime.fromtimestamp(int(timestamp)).strftime("%d/%m/%y %H:%M")
    values_list = [readable_time, *wave_pow, temp]
    if func == CAL:
        values_list.append(drift_rate)
        values_list.append("'{}'".format(real_cal_pt))
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
    sql = "INSERT INTO {}({}) VALUES ({})".format(func.lower() + str(table_id), ",".join(headers), values)
    try:
        cur.execute(sql)
        conn.commit()
    except sqlite3.OperationalError as e:  # TODO: Log this issue, column names have changed
        if "column" in e:
            return False
    conn.close()
    return True


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


def db_to_df(func, name):
    try:
        conn = sqlite3.connect(DB_PATH)
        cur = conn.cursor()
        cur.execute("SELECT {} from {} WHERE ProgName = '{}'".format("ID", "map", name))
        table_id = cur.fetchall()[0][0]
        df = pd.read_sql_query("SELECT * from {}".format(func.lower() + str(table_id)), conn)
        del df["ID"]
        conn.close()
        return df
    except (pd.io.sql.DatabaseError, sqlite3.OperationalError):
        return pd.DataFrame()


def create_data_coll(name, is_cal, snums=None):
    if snums is None:
        snums = get_snums(is_cal)
    try:
        func = BAKING
        if is_cal:
            func = CAL
        df = db_to_df(func, name)
        if is_cal:
            real_points_df = df[df['Real Point'] == 'True']
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
            if is_cal and len(real_points_df):
                data_coll.powers_real.append((real_points_df[pow_head]))
                data_coll.wavelens_real.append(real_points_df[wave_head])
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

        if is_cal:
            data_coll.drift_rates = df['Drift Rate']

        if is_cal and len(real_points_df):
            data_coll.timestamps_real = real_points_df["Date Time"]
            data_coll.times_real = [(time - start_time) / 60 / 60 for time in data_coll.timestamps_real]

            first_temp = list(real_points_df["Mean Temperature (K)"])[0]
            data_coll.temp_diffs_real = np.array([temp - first_temp for temp in real_points_df["Mean Temperature (K)"]])

            data_coll.wavelen_diffs_real = np.array([np.array([w - list(wave)[0] for w in wave])
                                                     for wave in data_coll.wavelens_real])
            data_coll.power_diffs_real = np.array([np.array([p - list(power)[0] for p in power])
                                                   for power in data_coll.powers_real])

            data_coll.mean_wavelen_diffs_real = np.array(data_coll.wavelen_diffs_real[0])
            data_coll.mean_power_diffs_real = np.array(data_coll.power_diffs_real[0])

            for wave_diff, pow_diff in zip(data_coll.wavelen_diffs_real[1:], data_coll.power_diffs_real[1:]):
                data_coll.mean_wavelen_diffs_real += wave_diff
                data_coll.mean_power_diffs_real += pow_diff

            data_coll.mean_wavelen_diffs_real /= len(data_coll.mean_wavelen_diffs_real)
            data_coll.mean_wavelen_diffs_real *= 1000
            data_coll.mean_power_diffs_real /= len(data_coll.mean_power_diffs_real)

            data_coll.real_points = df['Real Point']
        return data_coll, df
    except (KeyError, IndexError) as e:
        raise RuntimeError("No data has been collected yet")


def create_excel_file(xcel_file, snums, is_cal=False):
    """Creates an excel file from the correspoding csv file."""
    try:
        data_coll, df = create_data_coll(helpers.get_file_name(xcel_file), is_cal, snums)
        new_df = pd.DataFrame()
        small_df = pd.DataFrame()
        df_cal = pd.DataFrame()
        if is_cal:
            df_cal = df[df["Real Point"] == "True"]
            small_df["Date Time"] = df_cal["Date Time"].apply(lambda x: x.tz_localize("UTC").tz_convert("US/Eastern"))
        new_df["Date Time"] = df["Date Time"].apply(lambda x: x.tz_localize("UTC").tz_convert("US/Eastern"))

        headers = df.columns.values.tolist()
        wave_headers = [head for head in headers if "Wave" in head]
        pow_headers = [head for head in headers if "Pow" in head]
        temp_header = [h for h in headers if "Temperature" in h][0]

        if is_cal:
            small_df["{} Time (hr.)".format(u"\u0394")] = data_coll.times_real
            small_df[temp_header] = df_cal[temp_header]

        new_df["{} Time (hr.)".format(u"\u0394")] = data_coll.times
        new_df[temp_header] = df[temp_header]

        for col in wave_headers:
            new_df[col] = df[col]
            if is_cal:
                small_df[col] = df_cal[col]
        for col in pow_headers:
            new_df[col] = df[col]
            if is_cal:
                small_df[col] = df_cal[col]

        if not is_cal:
            new_df["{} Time (hr)  ".format(u"\u0394")] = data_coll.times
            new_df["{}T (K)  ".format(u"\u0394")] = data_coll.temp_diffs

        wave_diffs = data_coll.wavelen_diffs
        if not is_cal:
            for snum, delta_wave in zip(snums, wave_diffs):
                # new_df["{} {}{} (nm.)".format(snum, u"\u0394", u"\u03BB")] = delta_wave
                new_df["{} {}{} (pm.)".format(snum, u"\u0394", u"\u03BB")] = delta_wave * 1000

        if not is_cal:
            new_df["{} Time (hr) ".format(u"\u0394")] = data_coll.times
            new_df["{}T (K) ".format(u"\u0394")] = data_coll.temp_diffs

        power_diffs = data_coll.power_diffs
        if not is_cal:
            for snum, delta_pow in zip(snums, power_diffs):
                new_df["{} {}{} (dBm.)".format(snum, u"\u0394", "P")] = delta_pow

        if not is_cal:
            new_df["{}T (K)".format(u"\u0394")] = data_coll.temp_diffs
            new_df["Mean raw {}{} (pm.)".format(u"\u0394", u"\u03BB")] = data_coll.mean_wavelen_diffs
            new_df["Mean raw {}{} (dBm.)".format(u"\u0394", "P")] = data_coll.mean_power_diffs

        defaults = {'font_size': 14}
        sf_cal = StyleFrame(small_df, styler_obj=Styler(**defaults, shrink_to_fit=False, wrap_text=False))
        sf = StyleFrame(new_df, styler_obj=Styler(**defaults, shrink_to_fit=False, wrap_text=False))

        # Style the headers of the table
        header_style = Styler(bold=True, font_size=18)
        sf.set_column_width(columns=sf.columns, width=35)
        sf.apply_headers_style(styler_obj=header_style)
        if is_cal:
            sf_cal.set_column_width(columns=sf.columns, width=35)
            sf_cal.apply_headers_style(styler_obj=header_style)

        sf.apply_column_style(cols_to_style='Date Time',
                              styler_obj=Styler(number_format=utils.number_formats.date_time_with_seconds))
        if is_cal:
            sf_cal.apply_column_style(cols_to_style='Date Time',
                                      styler_obj=Styler(number_format=utils.number_formats.date_time_with_seconds))

        for snum, hex_color in zip(snums, HEX_COLORS):
            sf.apply_column_style(cols_to_style=[c for c in new_df.columns.values if snum in c],
                                  styler_obj=Styler(bg_color=hex_color))
            if is_cal:
                sf_cal.apply_column_style(cols_to_style=[c for c in small_df.columns.values if snum in c],
                                          styler_obj=Styler(bg_color=hex_color))

        sf.apply_column_style(cols_to_style="Mean Temperature (K)", styler_obj=Styler(font_color=utils.colors.red))
        sf.apply_column_style(cols_to_style=[c for c in new_df.columns.values if "{}T (K)".format(u"\u0394") in c],
                              styler_obj=Styler(font_color=utils.colors.red))

        if not is_cal:
            sf.apply_column_style(cols_to_style="Mean raw {}{} (pm.)".format(u"\u0394", u"\u03BB"),
                                  styler_obj=Styler(font_color=utils.colors.red))

        if is_cal:
            sf_cal.apply_column_style(cols_to_style="Mean Temperature (K)", styler_obj=Styler(font_color=utils.colors.red))
            sf_cal.apply_column_style(cols_to_style=[c for c in small_df.columns.values if "{}T (K)".format(u"\u0394") in c],
                                      styler_obj=Styler(font_color=utils.colors.red))

        ew = StyleFrame.ExcelWriter(xcel_file)
        if is_cal:
            sf_cal.to_excel(excel_writer=ew, row_to_add_filters=0, sheet_name="Cal")
            sf.to_excel(excel_writer=ew, row_to_add_filters=0, sheet_name="Full Cal")
        else:
            sf.to_excel(excel_writer=ew, row_to_add_filters=0, sheet_name="Sheet 1")
            sf.to_excel(excel_writer=ew, row_to_add_filters=0)
        ew.save()
        # Freeze the columns before column 'A' (=None) and rows above '2' (=1).
        # columns_and_rows_to_freeze='A2').save()
        os.startfile('"{}"'.format(xcel_file.replace("\\", "\\\\")))
    except RuntimeError:
        mbox.showwarning("Error creating Excel File",
                         "No data has been recorded yet, or the database has been corrupted.")
    except PermissionError:
        mbox.showwarning("Excel file is already opened",
                         "Please close {}, before attempting to create a new copy of it.".format(xcel_file))


def get_snums(is_cal):
    prog = BAKING
    if is_cal:
        prog = CAL
    cparser = configparser.ConfigParser()
    cparser.read(PROG_CONFIG_PATH)
    snums = []
    for i in range(4):
        snums.extend(cparser.get(prog, "chan{}_fbgs".format(i+1)).split(","))
    snums = [s for s in snums if s != '']
    return snums
