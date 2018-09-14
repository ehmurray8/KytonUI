"""Module used for helping with creating output files, and communicating with the database."""
import datetime
import os
import sqlite3
from tkinter import messagebox as mbox
import configparser
import pandas as pd
import queue
from typing import List
from StyleFrame import Styler, utils, StyleFrame
from fbgui import helpers
from fbgui.datatable import DataTable
from fbgui.constants import HEX_COLORS, CAL, BAKING, PROG_CONFIG_PATH, DB_PATH
from fbgui.messages import Message, MessageType
from fbgui.data_container import DataCollection


def write_db(file_name: str, serial_nums: List[str], timestamp: float, temp: float, wavelengths: List[float],
             powers: List[float], func: str, table: DataTable, main_queue: queue.Queue, drift_rate: float=None,
             real_cal_pt: bool=False, cycle_num: int=0) -> bool:
    """
    Writes the output to sqlite database.

    :param file_name: file name of the run of the program that data is being collected for
    :param serial_nums: serial numbers of the fbgs being used for the run
    :param timestamp: unix timestamp of when the data was recorded in s
    :param temp: temperature of the oven when the data was recorded
    :param wavelengths: list of wavelength readings to record
    :param powers: list of power readings to record
    :param func: program identifier string
    :param table: data table object to add the data points to as they are recorded in the table
    :param main_queue: queue used for adding logging messages to
    :param drift_rate: drift rate to record if the program is a calibration program
    :param real_cal_pt: boolean value whether or not this is an actual calibration point, used for calibration
    :param cycle_num: the calibration cycle number if the program is a calibration program
    :return: True if wrote data successfully, False otherwise
    """
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
        values_list.append(cycle_num)
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
    except sqlite3.OperationalError as e:
        try:
            if "column" in e:
                msg = Message(MessageType.ERROR, "Configuration Error",
                              "Serial numbers have changed from the first time this program was run. Please "
                              "use a new file name.")
                main_queue.put(msg)
                return False
        except TypeError as t:
            main_queue.put(Message(MessageType.DEVELOPER, "Write DB sqlite3 Error Dump", str(e)))
            main_queue.put(Message(MessageType.DEVELOPER, "Write DB Type Error Dump", str(t)))
    conn.close()
    return True


def get_last_cycle_num(file_name: str, func: str) -> int:
    """
    Get the number of the last calibration cycle that data is recorded for.

    :param file_name: the name of the file that the current program corresponds to
    :param func: program identifier string
    :return: last calibration cycle number, or 0 if there is no data calibration recorded
    """
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    name = helpers.get_file_name(file_name)
    try:
        cur.execute("SELECT ID FROM map WHERE ProgName = '{}';".format(name))
        table_id = cur.fetchall()[0][0]
    except (sqlite3.OperationalError, IndexError):
        conn.close()
        return 0
    table_name = func.lower() + str(table_id)
    cur.execute("SELECT {}.'Cycle Num' FROM {};".format(table_name, table_name))
    last_cycle_num = cur.fetchall()
    last_cycle_num = last_cycle_num[-1][0]
    conn.close()
    return int(last_cycle_num)


def program_exists(name: str, cur_map: sqlite3.Cursor, func: str) -> bool:
    """
    Checks whether or not there is data in the database for the program of type func, named name.

    :param name: the name of the current running program run
    :param cur_map: the map table database cursor
    :param func: the program identifier string
    :return: True if the program exists, otherwise False
    """
    try:
        cur_map.execute("SELECT ID, ProgName, ProgType from map")
        rows = cur_map.fetchall()
    except sqlite3.OperationalError:
        return False

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


def create_headers(snums: List[str], is_cal: bool, formatted: bool) -> List[str]:
    """
    Create the data column headers.

    :param snums: serial numbers for the current program run
    :param is_cal: True if the current program run is a calibration run, False otherwise
    :param formatted: True if headers are using facing, False if headers are used for the database
    :return: list of header strings
    """
    snum_cols = []
    for snum in snums:
        snum_cols.append("'{} Wavelength (nm.)'".format(snum))
        snum_cols.append("'{} Power (dBm.)'".format(snum))
    col_list = ["ID", "'Date Time'", *snum_cols, "'Mean Temperature (K)'"]
    if is_cal:
        col_list.append("'Drift Rate'")
        col_list.append("'Real Point'")
        col_list.append("'Cycle Num'")
    if formatted:
        col_list = [s.replace("'", "") for s in col_list]
    return col_list


def create_headers_init(snums: List[str], is_cal: bool) -> List[str]:
    """
    Returns a list of strings used for creating the database attribute values, includes names and SQL types.

    :param snums: serial numbers being used in the current program run
    :param is_cal: True if the program is a calibration run, False otherwise
    :return: list of comma separated strings, names and types of table attributes
    """
    snum_cols = []
    for snum in snums:
        snum_cols.append("'{} Wavelength (nm.)' REAl NOT NULL".format(snum))
        snum_cols.append("'{} Power (dBm.)' REAL NOT NULL".format(snum))
    col_list = ["ID INTEGER NOT NULL PRIMARY KEY", "'Date Time' REAL NOT NULL",
                *snum_cols, "'Mean Temperature (K)' REAL NOT NULL"]
    if is_cal:
        col_list.append("'Drift Rate' REAL NOT NULL")
        col_list.append("'Real Point' INTEGER NOT NULL")
        col_list.append("'Cycle Num' INTEGER NOT NULL")
    return col_list


# noinspection PyUnresolvedReferences
def db_to_df(func: str, name: str) -> pd.DataFrame:
    """
    Creates a pandas dataframe object from the database table corresponding to the program run of type
    func, and named name.

    :param func: program identifier string
    :param name: name of the program run
    :return: dataframe for the specified table, or an empty dataframe if one cannot be created for the table
    :raises IndexError: If program is not in the map, thus data has not been recorded for this program yet
    :raises RuntimeError: If program database has been corrupted, or the table is empty
    """
    conn = None
    try:
        conn = sqlite3.connect(DB_PATH)
        cur = conn.cursor()
        cur.execute("SELECT {} from map WHERE ProgName = '{}'".format("ID", name))
        table_id = cur.fetchall()[0][0]
        df = pd.read_sql_query("SELECT * from {}".format(func.lower() + str(table_id)), conn)
        del df["ID"]
        conn.close()
        return df
    except (pd.io.sql.DatabaseError, sqlite3.OperationalError):
        if conn is not None:
            conn.close()
        return pd.DataFrame()
    except (RuntimeError, IndexError) as e:
        if conn is not None:
            conn.close()
        raise e


def make_length(values: List, length: int) -> List:
    """
    Force the values list to be of length, length.

    :param values: list to resize
    :param length: required length of the list
    :return: list of length, length
    """
    values = values[:length]
    values += [0] * (length - len(values))
    return values


def create_excel_file(xcel_file: str, snums: List[str], main_queue: queue.Queue, is_cal=False):
    """
    Create an excel file using the xcel_file to get data from the corresponding sql table.

    :param xcel_file: name of the excel file for the program to create the excel file for
    :param snums: list of serial numbers to use for creating the excel file
    :param main_queue: queue to use for posting logging messages to
    :param is_cal: True if creating an excel file for a calibration program run, False otherwise
    """
    try:
        name = helpers.get_file_name(xcel_file)
        prog = CAL if is_cal else BAKING
        df = db_to_df(prog, name)
        data_coll = DataCollection()
        data_coll.create(is_cal, df, snums, main_queue)
        new_df = pd.DataFrame()
        small_df = pd.DataFrame()
        df_cal = pd.DataFrame()
        cycles = []
        if is_cal:
            df_cal = df[df["Real Point"] == "True"]
            cycles = list(set(df_cal["Cycle Num"]))
            cycles.sort()
        new_df["Date Time"] = df["Date Time"].apply(lambda x: x.tz_localize("UTC").tz_convert("US/Eastern"))

        headers = df.columns.values.tolist()
        wave_headers = [head for head in headers if "Wave" in head]
        pow_headers = [head for head in headers if "Pow" in head]
        temp_header = [h for h in headers if "Temperature" in h][0]

        new_df["{} Time (hr.)".format(u"\u0394")] = data_coll.times
        new_df[temp_header] = df[temp_header]

        for col in wave_headers:
            new_df[col] = df[col]
            if is_cal and "Cycle Num" not in df_cal.columns.values:
                small_df[col] = df_cal[col]
        for col in pow_headers:
            new_df[col] = df[col]
            if is_cal and "Cycle Num" not in df_cal.columns.values:
                small_df[col] = df_cal[col]

        temps_avg = []
        if is_cal and "Cycle Num" in df_cal.columns.values:
            for cycle_num in cycles:
                temps = list(df_cal[df_cal["Cycle Num"] == cycle_num][temp_header])
                if not len(temps_avg):
                    temps_avg = temps
                else:
                    temps += [0] * (len(temps_avg) - len(temps))
                    temps_avg = [(t + new_t)/2. if new_t != 0 else t for t, new_t in zip(temps_avg, temps)]
                small_df["Temperature (K) {}".format(cycle_num)] = make_length(list(temps), len(temps_avg))
                for col in wave_headers:
                    waves = df_cal[df_cal["Cycle Num"] == cycle_num][col]
                    small_df[col + " {}".format(cycle_num)] = make_length(list(waves), len(temps_avg))
            small_df["Mean Temperature (K)"] = make_length(list(temps_avg), len(temps_avg))
            for cycle_num in cycles:
                temps = list(df_cal[df_cal["Cycle Num"] == cycle_num][temp_header])
                small_df["Temperature (K) {} ".format(cycle_num)] = make_length(list(temps), len(temps_avg))
                for col in pow_headers:
                    pows = df_cal[df_cal["Cycle Num"] == cycle_num][col]
                    small_df[col + " {}".format(cycle_num)] = make_length(list(pows), len(temps_avg))

        small_df["Mean Temperature (K) "] = list(temps_avg)

        if not is_cal:
            new_df["{} Time (hr)  ".format(u"\u0394")] = data_coll.times
            new_df["{}T (K)  ".format(u"\u0394")] = data_coll.delta_temps

        wave_diffs = data_coll.delta_wavelengths_pm
        if not is_cal:
            for snum, delta_wave in zip(snums, wave_diffs):
                new_df["{} {}{} (pm.)".format(snum, u"\u0394", u"\u03BB")] = delta_wave

        if not is_cal:
            new_df["{} Time (hr) ".format(u"\u0394")] = data_coll.times
            new_df["{}T (K) ".format(u"\u0394")] = data_coll.delta_temps

        power_diffs = data_coll.delta_powers
        if not is_cal:
            for snum, delta_pow in zip(snums, power_diffs):
                new_df["{} {}{} (dBm.)".format(snum, u"\u0394", "P")] = delta_pow

        if not is_cal:
            new_df["{}T (K)".format(u"\u0394")] = data_coll.delta_temps
            new_df["Mean raw {}{} (pm.)".format(u"\u0394", u"\u03BB")] = data_coll.mean_delta_wavelengths_pm
            new_df["Mean raw {}{} (dBm.)".format(u"\u0394", "P")] = data_coll.mean_delta_powers

        defaults = {'font_size': 14}
        sf_cal = StyleFrame(small_df, styler_obj=Styler(**defaults, shrink_to_fit=False, wrap_text=False))
        sf = StyleFrame(new_df, styler_obj=Styler(**defaults, shrink_to_fit=False, wrap_text=False))

        header_style = Styler(bold=True, font_size=18)
        sf.set_column_width(columns=sf.columns, width=35)
        sf.apply_headers_style(styler_obj=header_style)
        if is_cal:
            sf_cal.set_column_width(columns=sf_cal.columns, width=35)
            sf_cal.apply_headers_style(styler_obj=header_style)

        sf.apply_column_style(cols_to_style='Date Time',
                              styler_obj=Styler(number_format=utils.number_formats.date_time_with_seconds))

        for snum, hex_color in zip(snums, HEX_COLORS):
            sf.apply_column_style(cols_to_style=[c for c in new_df.columns.values if snum in c],
                                  styler_obj=Styler(bg_color=hex_color))
            if is_cal:
                sf_cal.apply_column_style(cols_to_style=[c for c in small_df.columns.values if snum in c],
                                          styler_obj=Styler(bg_color=hex_color))

        sf.apply_column_style(cols_to_style=[col for col in df.columns.values if "Temperature" in col],
                              styler_obj=Styler(font_color=utils.colors.red))
        sf.apply_column_style(cols_to_style=[c for c in new_df.columns.values if "{}T (K)".format(u"\u0394") in c],
                              styler_obj=Styler(font_color=utils.colors.red))

        if not is_cal:
            sf.apply_column_style(cols_to_style="Mean raw {}{} (pm.)".format(u"\u0394", u"\u03BB"),
                                  styler_obj=Styler(font_color=utils.colors.red))

        if is_cal:
            sf_cal.apply_column_style(cols_to_style=[col for col in small_df.columns.values if "Temperature" in col],
                                      styler_obj=Styler(font_color=utils.colors.red))
            sf_cal.apply_column_style(cols_to_style=[c for c in small_df.columns.values
                                                     if "{}T (K)".format(u"\u0394") in c],
                                      styler_obj=Styler(font_color=utils.colors.red))

        ew = StyleFrame.ExcelWriter(xcel_file)
        if is_cal:
            sf_cal.to_excel(excel_writer=ew, row_to_add_filters=0, sheet_name="Cal")
            sf.to_excel(excel_writer=ew, row_to_add_filters=0, sheet_name="Full Cal")
        else:
            sf.to_excel(excel_writer=ew, row_to_add_filters=0, sheet_name="Sheet 1")
        ew.save()
        os.startfile('"{}"'.format(xcel_file.replace("\\", "\\\\")))
    except (RuntimeError, IndexError):
        main_queue.put(Message(MessageType.WARNING, "Excel File Creation Error",
                               "No data has been recorded yet, or the database has been corrupted."))
    except PermissionError:
        main_queue.put(Message(MessageType.WARNING, "Excel File Creation Error",
                               "Please close {}, before attempting to create a new copy of it.".format(xcel_file)))
        mbox.showwarning("Excel file is already opened",
                         "Please close {}, before attempting to create a new copy of it.".format(xcel_file))


def get_snums(is_cal: bool) -> List[str]:
    """
    Get the serial numbers recorded in the prog_config configuration file, under the header
    based on the is_cal parameter

    :param is_cal: True if program is calibration, False otherwise
    :return: list of serial numbers
    """
    program = BAKING
    if is_cal:
        program = CAL
    parser = configparser.ConfigParser()
    parser.read(PROG_CONFIG_PATH)
    serial_nums = []
    for i in range(4):
        serial_nums.extend(parser.get(program, "chan{}_fbgs".format(i+1)).split(","))
    serial_nums = [s for s in serial_nums if s != '']
    return serial_nums
