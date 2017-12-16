"""Module used for helping with creating output files."""
# pylint: disable=import-error, relative-import
# pylint: disable-msg=too-many-arguments, too-many-branches, too-many-locals

import os
import time
import platform
import stat
import threading
import configparser
from tkinter import messagebox
import xlsxwriter
import pandas as pd
import data_container as datac
import options_frame


HEX_COLORS = ["#FFD700", "#008080", "#FF7373", "#FFC0CB",
              "#40E0D0", "#FFA500", "#00FF00", "#468499",
              "#66CDAA", "#FF7F50", "#FF4040", "#B4EEB4",
              "#DAA520", "#FFFF00", "#C0C0C0", "#F0F8FF",
              "#E6E6FA", "#008000", "#FF00FF", "#0099CC"]

LOCK = threading.Lock()

BAKING_SECTION = "Baking"
CAL_SECTION = "Calibration"


def write_csv_file(file_name, serial_nums, timestamp, temp, wavelengths, powers,
                   func, drift_rate=None, real_cal_pt=False):
    """Writes the output csv file."""

    file_name = os.path.splitext(file_name)[0] + '.csv'

    LOCK.acquire()
    if os.path.isfile(file_name):
        if platform.system() != "Linux":
            os.chmod(file_name, stat.S_IRWXU)
        file_obj = open(file_name, "a")
    else:
        try:
            file_obj = open(file_name, "w")
        except FileNotFoundError:
            os.mkdir(os.path.dirname(file_name), os.W_OK)
            file_obj = open(file_name, "w")

        if func == options_frame.BAKING:
            header = "Metadata\n"
        else:
            header = "Caldata\n"

        file_obj.write(header)
        file_obj.write(",".join(serial_nums))
        file_obj.write("\n")
        wave_total = sum(wavelengths)
        file_obj.write(",".join(str(x) for x in wavelengths))
        wave_total /= len(serial_nums)
        file_obj.write("\n" + str(round(timestamp, 5)) + ",")
        file_obj.write(str(wave_total) + "," + str(temp + 273.15) + "\n\n")

        line = "Serial Num,Timestamp(s),Temperature(K),Wavelength(nm),Power(dBm)"
        if func == options_frame.CAL:
            line += ",Real Point,Drift Rate(mK/min)"
        line += "\n\n"
        file_obj.write(line)

    for snum, wave, power in zip(serial_nums, wavelengths, powers):
        line = str(snum) + "," + str(timestamp) + "," + str(temp) + "," +\
            str(wave) + "," + str(power)
        if func == options_frame.CAL:
            line += ", " + str(drift_rate) + ", " + str(real_cal_pt)
        file_obj.write("".join([line, "\n"]))

    file_obj.write("\n\n")
    file_obj.close()
    LOCK.release()
    if platform.system() != "Linux":
        os.chmod(file_name, stat.S_IREAD)


def parse_csv_file(csv_file):
    """Parses defined csv file."""
    if platform.system() != "Linux":
        os.chmod(csv_file, stat.S_IWRITE)

    try:
        entries_df = pd.read_csv(csv_file, header=4, skip_blank_lines=True)
    except pd.errors.ParserError:
        raise IOError("Fatal error csv file has been corrupted.")

    mdata = datac.Metadata()

    # Read Metadata
    LOCK.acquire()
    with open(csv_file) as csv:
        csv.readline()
        mdata.serial_nums = csv.readline().split(",")
        mdata.serial_nums = [snum.replace('\n', '')
                             for snum in mdata.serial_nums]

        mdata.start_wavelens = csv.readline().split(",")
        mdata.start_wavelens = [wave.replace(
            '\n', '') for wave in mdata.start_wavelens]

        start_time_wavelen_temp = csv.readline().split(",")
        start_time_wavelen_temp = [num.replace(
            '\n', '') for num in start_time_wavelen_temp]
        csv.close()

    mdata.start_time = float(start_time_wavelen_temp[0])
    mdata.start_wavelen_avg = float(start_time_wavelen_temp[1])
    mdata.start_temp = float(start_time_wavelen_temp[2])
    if platform.system() != "Linux":
        os.chmod(csv_file, stat.S_IWRITE)
    LOCK.release()
    return mdata, entries_df


def __create_headers(serial_nums, worksheet, num_cols, is_cal=False):
    worksheet.set_column(0, num_cols, 25)
    headers = ["Date Time", u'\u0394' + "Time (hrs.)"]
    for snum in serial_nums:
        headers.append(str(snum) + " Wavelength (nm.)")
        headers.append(str(snum) + " Power (dBm.)")
    headers.append("Mean Temp (K)")
    for snum in serial_nums:
        headers.append(str(snum) + " " + u'\u0394\u03BB' +
                       ", from start (nm.)")
    headers.append(u'\u0394' + "T, from start (K)")
    headers.append("Mean raw " + u'\u0394\u03BB' + ", from start (pm.)")
    if is_cal:
        headers.append("Drift Rate (mK/min)")
    return headers


def create_data_coll(mdata, entries_df, is_cal=False, dataq=None):
    """Gathers the data from the csv file, and stores it in a DataCollection object."""
    data_coll = datac.DataCollection()

    times = entries_df['Timestamp(s)'].values.tolist()
    for idx, time_num in enumerate(times):
        if idx % len(mdata.serial_nums) == 0:
            data_coll.times.append(round(time_num, 5))

    temps = entries_df['Temperature(K)'].values.tolist()
    for idx, temp in enumerate(temps):
        if idx % len(mdata.serial_nums) == 0:
            data_coll.temps.append(temp + 273.15)
            data_coll.temp_diffs.append(
                float(temp) + 273.15 - float(mdata.start_temp))

    if is_cal:
        data_coll.drift_rates = entries_df['Drift Rate(mK/min)'].values.tolist()

        data_coll.real_points = entries_df['Real Point'].values.tolist()

    wavelens = entries_df['Wavelength(nm)'].values.tolist()

    data_coll.wavelens = [[] for _ in range(len(mdata.serial_nums))]
    for idx, wavelen in enumerate(wavelens):
        data_coll.wavelens[int(idx % len(mdata.serial_nums))].append(wavelen)

    powers = entries_df['Power(dBm)'].values.tolist()
    data_coll.powers = [[] for _ in range(len(mdata.serial_nums))]
    for idx, power in enumerate(powers):
        data_coll.powers[int(idx % len(mdata.serial_nums))].append(power)
    start_powers = []
    for power in data_coll.powers:
        start_powers.append(power[0])

    data_coll.wavelen_diffs = [[] for _ in range(len(mdata.serial_nums))]
    data_coll.power_diffs = [[] for _ in range(len(mdata.serial_nums))]
    for row_num, time_num in enumerate(data_coll.times):
        total_diff_w = 0
        total_diff_p = 0
        for idx, (wavelen, power) in enumerate(zip(data_coll.wavelens, data_coll.powers)):
            diff_w = round(float(wavelen[row_num]), 5) - \
                float(mdata.start_wavelens[idx])
            diff_p = round(float(power[row_num]), 5) - float(start_powers[idx])
            total_diff_w += diff_w
            total_diff_p += diff_p
            data_coll.wavelen_diffs[idx].append(diff_w)
            data_coll.power_diffs[idx].append(diff_p)

        total_diff_w /= len(mdata.serial_nums)
        total_diff_p /= len(mdata.serial_nums)

        data_coll.mean_wavelen_diffs.append(total_diff_w * 1000)
        data_coll.mean_power_diffs.append(total_diff_p)

    if dataq is not None:
        dataq.put(data_coll)
    else:
        return data_coll


# pylint: disable=unused-argument
def __create_row_strs(mdata, entries_df, is_cal=False):
    data_coll = create_data_coll(mdata, entries_df, is_cal)

    row_num = 0
    row_strs = []
    for time_num, temp in zip(data_coll.times, data_coll.temps):
        row_strs.append([])
        row_strs[row_num].append(
            time.strftime("%a, %d %b %Y %H:%M:%S", time.localtime(time_num)))
        row_strs[row_num].append(round(time_num / 3600 -
                                       mdata.start_time / 3600, 5))

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


def __create_formats(serial_nums, workbook, is_cal=False):
    color_formats = []
    bold_color_formats = []
    for _, color in zip(serial_nums, HEX_COLORS):
        format_col = workbook.add_format({'bg_color': color})
        color_formats.append(format_col)
        bold_format = workbook.add_format({'bg_color': color, 'bold': True, 'font_size': 16})
        bold_color_formats.append(bold_format)

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
    chart = workbook.add_chart({'type': 'scatter',
                                'subtype': 'smooth_with_markers'})
    cats = "=Sheet1!$B$2:$B$" + str(len(entries) + 1)
    val_col = num_to_excel_col((len(serial_nums) * 3) + 4)
    vals = "=Sheet1!$" + val_col + "$2:$" + \
        val_col + "$" + str(len(entries) + 1)
    line_name = "Raw " + u'\u0394\u03BB' + "pm"
    chart.add_series({'name': line_name, 'categories': cats, 'values': vals})
    chart.set_title({'name': 'Baking: ' + u'\u0394\u03BB' +
                             " (pm) vs. Time (hr) from start"})
    chart.set_y_axis({'name': u'\u0394\u03BB' + " average (pm)"})
    chart.set_x_axis({'name': 'Elapsed Time from start (hr)'})

    chart.set_style(10)
    col_name = num_to_excel_col(num_cols + 2)
    worksheet.insert_chart("${}$3".format(col_name), chart)
    return num_cols + 12


def __create_chart_dr(data_coll, worksheet, workbook, col_start):
    chart = workbook.add_chart(
        {'type': 'scatter', 'subtype': 'smooth_with_markers'})

    times_real = []
    drates_real = []
    for time_num, drate in zip(data_coll.times, data_coll.drift_rates):
        times_real.append(time_num)
        drates_real.append(drate)

    chart.add_series({'name': 'Average Drift Rate (mK/min)', 'categories': times_real,
                      'values': data_coll.drates_real})
    chart.set_title({'name': 'Average Drift Rate (mK/min) vs. Time(hr)'})
    chart.set_y_axis({'name': 'Average Drift Rate (mK/min)'})
    chart.set_x_axis({'name': 'Time (hr)'})

    chart.set_style(10)
    worksheet.insert_chart("${}$3".format(num_to_excel_col(col_start)), chart)


def create_excel_file(xcel_file, is_cal=False):
    """Creates an excel file from the correspoding csv file."""

    csv_file = os.path.splitext(xcel_file)[0]+'.csv'

    if os.path.isfile(csv_file):
        mdata, entries_df = parse_csv_file(csv_file)
        num_cols = len(mdata.serial_nums) * 3 + 5

        workbook = xlsxwriter.Workbook(xcel_file)
        worksheet = workbook.add_worksheet()

        headers = __create_headers(
            mdata.serial_nums, worksheet, num_cols, is_cal)

        row_strs, data_coll = __create_row_strs(mdata, entries_df, is_cal)

        row_format, row_header_format = __create_formats(
            mdata.serial_nums, workbook, is_cal)

        bold_format = workbook.add_format()
        bold_format.set_bold()

        __write_headers(headers, row_header_format, bold_format, worksheet)

        __write_rows(row_strs, row_format, worksheet,
                     bold_format, data_coll, is_cal)

        worksheet.set_column(0, num_cols, 37)

        col_end = __create_chart(
            entries_df, mdata.serial_nums, num_cols, worksheet, workbook)

        if is_cal:
            __create_chart_dr(data_coll, worksheet, workbook, col_end)

        workbook.close()
        os.system("start " + xcel_file)


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


def on_closing(root, old_conf, widgets):
    """Stops the user from closing if they haven't saved."""
    unsaved = False
    for old_c, widg in zip(old_conf, widgets):
        if old_c != widg.get():
            unsaved = True
            break

    if unsaved:
        if messagebox.askyesno("Quit", "Changes won't be save. Are you sure you want to quit?"):
            root.destroy()
        else:
            root.tkraise()
    else:
        root.destroy()


if __name__ == "__main__":
    create_excel_file("kyton_out.csv")
