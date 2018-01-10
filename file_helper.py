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

    wave_pow_heads = []
    for snum in snums:
        wave_pow_heads.append("{} Wavelength (nm.)".format(snum))
        wave_pow_heads.append("{} Power (dBm.)".format(snum))

    headers = ["Date Time", "{} Time (hrs.)".format(u"\u0394"), *wave_pow_heads, "Mean Temperature (K)"]
    return pd.DataFrame(data={h: d for h, d in zip(headers, rows)})


def create_data_coll(name, snums, is_cal):
    df = db_to_df(name, snums, is_cal)
    data_coll = datac.DataCollection()
    headers = create_headers(snums, is_cal)
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
    return data_coll, df


def create_excel_file(xcel_file, snums, is_cal=False):
    """Creates an excel file from the correspoding csv file."""

    wb = openpyxl.Workbook()
    ws = wb.active

    data_coll, df = create_data_coll(help.get_file_name(xcel_file), snums, is_cal)
    for snum, delta_wave in zip(snums, data_coll.wavelen_diffs):
        df["{} {}{}, from start (nm).".format(snum, u"\u0394", u"\u03BB")] = delta_wave

    df["{}T, from start (K)"] = data_coll.temp_diffs
    df["Mean raw {}{}, from start (pm.)".format(u"\u0394", u"\u03BB")] = data_coll.mean_wavelen_diffs

    for r in openpyxl.utils.dataframe.dataframe_to_rows(df, index=True, header=True):
        ws.append(r)

    for cell in ws['A'] + ws[1]:
        cell.style = 'Pandas'

    wb.save(xcel_file)


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
