"""Module used for helping with creating output files."""
import os
import time
import xlsxwriter

HEX_COLORS = ["#FFD700", "#008080", "#FF7373", "#FFC0CB",
              "#40E0D0", "#FFA500", "#00FF00", "#468499",
              "#66CDAA", "#FF7F50", "#FF4040", "#B4EEB4",
              "#DAA520", "#FFFF00", "#C0C0C0", "#F0F8FF",
              "#E6E6FA", "#008000", "#FF00FF", "#0099CC"]


def write_csv_file(file_name, serial_nums, timestamp, temp, wavelengths, powers):
    #pylint: disable-msg=too-many-arguments
    """Write the output csv file."""
    if os.path.isfile(file_name):
        file_obj = open(file_name, "a")
    else:
        file_obj = open(file_name, "w")
        file_obj.write("Metadata\n")
        need_comma = False
        for snum in serial_nums:
            if need_comma:
                file_obj.write(",")
            else:
                need_comma = True
            file_obj.write(snum)
        file_obj.write("\n" + str(timestamp) + ",")
        need_comma = False
        wave_total = 0
        for wave in wavelengths:
            if need_comma:
                file_obj.write(",")
            else:
                need_comma = True
            wave_total += float(wave)
            file_obj.write(str(wave))
        wave_total /= len(serial_nums)
        file_obj.write(str(wave_total) + "," + str(temp) + "\n")
        file_obj.write("Serial Num, Timestamp(s), Temperature (C), "\
                + "Wavelength (nm), Power (dBm)\n")

    i = 0
    while i < len(serial_nums):
        file_obj.write(str(serial_nums[i]) + "," + str(timestamp) + "," + str(temp) + "," +\
                    str(wavelengths[i]) + "," + str(powers[i]) + "\n")
        i += 1

    file_obj.write("\n\n")
    file_obj.close()

def __init_excel_file(csv_file):
    xcel_file = csv_file[:-3] + "xlsx"
    if os.path.isfile(xcel_file):
        os.remove(xcel_file)
    return xcel_file


def __parse_csv_file(csv_file):
    with open(csv_file) as f_obj:
        lines = f_obj.readlines()
        f_obj.close()

    metadata = lines[1:4]
    serial_nums = metadata[0].split(",")
    time_wave_temp = metadata[1].split(",")
    waves = metadata[2].split(",")

    start_time = float(time_wave_temp[0])
    start_wave = float(time_wave_temp[1])
    start_temp = float(time_wave_temp[2]) + 273.15

    lines = lines[7:]

    words_list = []
    for line in lines:
        words_list.append(line.split(","))

    entries = []
    while len(words_list) > len(serial_nums):
        entries.append(words_list[:len(serial_nums)])
        words_list = words_list[len(serial_nums)+2:]
    return serial_nums, start_time, start_wave, waves, start_temp, entries

def __create_headers(serial_nums, worksheet, num_cols):
    worksheet.set_column(0, num_cols, 25)
    headers = ["Date Time", u'\u0394' + "Time (hrs.)"]
    for snum in serial_nums:
        headers.append(str(snum) + " Wavelength (nm.)")
        headers.append(str(snum) + " Power (dBm.)")
    headers.append("Mean Temp (K)")
    for snum in serial_nums:
        headers.append(str(snum) + " " + u'\u0394\u03BB' + ", from start (nm.)")
    headers.append(u'\u0394' + "T, from start (K)")
    headers.append("Mean raw " + u'\u0394\u03BB' + ", from start (pm.)")
    return headers

def __create_row_strs(entries, start_temp, start_time, start_wave, waves, serial_nums):
    row_strs = [[]]
    row_num = 0
    for entry in entries:
        row_strs.append([])
        curr_entry_time = entry[0][1]
        curr_entry_time = curr_entry_time.replace(" ", "")
        curr_entry_time = float(curr_entry_time)
        curr_entry_temp = float(entry[0][2]) + 273.15
        row_strs[row_num].append(
            time.strftime("%a, %d %b %Y %H:%M:%S", time.localtime(curr_entry_time)))
        row_strs[row_num].append(round((float(curr_entry_time) - float(start_time)) / 3600, 5))
        wavelengths = []
        for data_pt in entry:
            row_strs[row_num].append(data_pt[3])
            wavelengths.append(data_pt[3])
            row_strs[row_num].append(data_pt[4])
        row_strs[row_num].append(curr_entry_temp)
        wave_total = 0
        for wave, begin_wave in zip(wavelengths, waves):
            row_strs[row_num].append(float(float(wave) - float(begin_wave)))
            wave_total += float(wave)
        row_strs[row_num].append(float(curr_entry_temp) - float(start_temp))
        wave_total /= len(serial_nums)
        row_strs[row_num].append((float(wave_total) - float(start_wave)) * 1000)
        row_num += 1
    return row_strs

def __create_formats(serial_nums, workbook):
    color_formats = []
    bold_color_formats = []
    for color in HEX_COLORS:
        format_col = workbook.add_format()
        format_col.set_bg_color(color)
        color_formats.append(format_col)
        bold_format = workbook.add_format()
        bold_format.set_bg_color(color)
        bold_format.set_bold()
        bold_color_formats.append(bold_format)

    row_format = [None, None]
    row_header_format = [None, None]
    sn_num = 0
    while sn_num < len(serial_nums):
        row_format.append(color_formats[sn_num])
        row_format.append(color_formats[sn_num])
        row_header_format.append(bold_color_formats[sn_num])
        row_header_format.append(bold_color_formats[sn_num])
        sn_num += 1

    format_red = workbook.add_format()
    format_red.set_font_color('red')
    format_b = workbook.add_format()
    format_b.set_font_color('red')
    format_b.set_bold()

    row_format.append(format_red)
    row_header_format.append(format_b)

    sn_num = 0
    while sn_num < len(serial_nums):
        row_format.append(None)
        row_header_format.append(None)
        sn_num += 1

    row_format.append(format_red)
    row_format.append(None)

    row_header_format.append(format_b)
    row_header_format.append(None)

    bold_format = workbook.add_format()
    bold_format.set_bold()
    return row_format, row_header_format, bold_format

def __write_headers(headers, row_header_format, bold_format, worksheet):
    col = 0
    for header, row_f in zip(headers, row_header_format):
        if row_f is None:
            worksheet.write(0, col, header, bold_format)
        else:
            worksheet.write(0, col, header, row_f)
        col += 1

def __write_rows(row_strs, row_format, worksheet):
    row_num = 1
    for row in row_strs:
        col = 0
        for num in row:
            if row_format[col] is None:
                worksheet.write(row_num, col, num)
            else:
                worksheet.write(row_num, col, num, row_format[col])
            col += 1
        row_num += 1

def __create_chart(entries, serial_nums, num_cols, worksheet, workbook):
    chart = workbook.add_chart({'type': 'scatter',
                                'subtype': 'smooth_with_markers'})
    cats = "=Sheet1!$B$2:$B$" + str(len(entries) + 1)
    val_col = num_to_excel_col((len(serial_nums) * 3) + 4)
    vals = "=Sheet1!$" + val_col  + "$2:$" + val_col + "$" + str(len(entries) + 1)
    line_name = "Raw " + u'\u0394\u03BB' + "pm"
    chart.add_series({'name': line_name, 'categories':cats, 'values':vals})
    chart.set_title({'name': 'Baking: ' + u'\u0394\u03BB' + " (pm) vs. Time (hr) from start"})
    chart.set_y_axis({'name': u'\u0394\u03BB' + " average (pm)"})
    chart.set_x_axis({'name': 'Elapsed Time from start (hr)'})

    chart.set_style(10)
    col_name = num_to_excel_col(num_cols + 1) + "3"
    worksheet.insert_chart(col_name, chart)

def create_excel_file(csv_file):
    """Creates an excel file from the correspoding csv file."""
    xcel_file = __init_excel_file(csv_file)

    if os.path.isfile(csv_file):
        serial_nums, start_time, start_wave, waves, start_temp, entries \
                    = __parse_csv_file(csv_file)
        num_cols = len(serial_nums) * 3 + 5

        workbook = xlsxwriter.Workbook(xcel_file)
        worksheet = workbook.add_worksheet()

        headers = __create_headers(serial_nums, worksheet, num_cols)

        row_strs = __create_row_strs(entries, start_temp, start_time, \
                    start_wave, waves, serial_nums)

        row_format, row_header_format, bold_format = __create_formats(serial_nums, workbook)

        __write_headers(headers, row_header_format, bold_format, worksheet)

        __write_rows(row_strs, row_format, worksheet)

        __create_chart(entries, serial_nums, num_cols, worksheet, workbook)

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
