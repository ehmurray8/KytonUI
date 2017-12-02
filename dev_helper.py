"""
Gets the amplitude and wavelength data using the Mircon Optics SM125,
and the Optical Switch.
"""
# pylint: disable=import-error, relative-import
import socket
import time
import functools


def avg_waves_amps(laser, switch, switches, num_pts, after_func):
    """Gets the average wavelengths and powers, updates data_pts."""
    lens = list(map(lambda x: len(x), switches))
    switches_arr = functools.reduce(lambda x, y: x+y, switches)
    switch_num = -1
    if len(switches_arr):
        switch_num = lens.index(max(lens))
    return __get_average_data(laser, switch, switches_arr, num_pts, switch_num, after_func)


def __avg_arr(first, second):
    temp = functools.reduce(lambda x, y: x+y, second)
    print("Second (2d?): {}, Second (1d): {}".format(second, temp))
    if len(functools.reduce(lambda x, y: x+y, second)):
        for i, row in enumerate(second):
            for j, col in enumerate(row):
                first[i][j] += col
                first[i][j] /= 2
    return first


def __get_data(laser, op_switch, switches_arr, switch_num, after_func):
    wavelens = [[], [], [], []]
    amps = [[], [], [], []]
    for switch in switches_arr:
        try:
            op_switch.set_channel(switch)
            #after_func(1250, lambda: __get_sm125_data(wavelens, amps, switch_num, laser))
            time.sleep(1.2)
            __get_sm125_data(wavelens, amps, switch_num, laser)
        except socket.error:
            pass
    return wavelens, amps


def __get_sm125_data(all_waves, all_amps, switch_num,  sm125):
    wavelens, amps, lens = sm125.get_data()
    first_run = True
    try:
        if len(functools.reduce(lambda x, y: x+y, all_waves)):
            first_run = False
    except Exception as e:
        print(str(e))
    for i, (amp, wave) in enumerate(zip(amps, wavelens)):
        if first_run or i == switch_num:
            all_waves[i].append(wave)
            all_amps[i].append(amp)
        else:
            temp_wave = all_waves[i].pop(0)
            temp_amp = all_amps[i].pop(0)
            all_waves[i].insert(0, (temp_wave + wave)/2.)
            all_amps[i].insert(0, (temp_amp + amp)/2.)


def __get_average_data(laser, op_switch, switches_arr, num_readings, switch_num, after_func):
    all_waves = [[], [], [], []]
    all_amps = [[], [], [], []]
    for i in range(num_readings):
        wavelengths, amplitudes = __get_data(laser, op_switch, switches_arr, switch_num, after_func)
        print("Wavelengths {}".format(str(wavelengths)))
        print("Amplitudes {}".format(str(amplitudes)))
        all_waves = __avg_arr(wavelengths, all_waves)
        all_amps = __avg_arr(amplitudes, all_amps)
    return functools.reduce(lambda x, y: x+y, all_waves), functools.reduce(lambda x, y: x+y, all_amps)
