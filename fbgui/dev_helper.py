"""
Gets the amplitude and wavelength data using the Mircon Optics SM125,
and the Optical Switch.
"""
import socket
import time
import numpy as np


def avg_waves_amps(laser, switch, switches, num_pts, pos_used, use_dev, num_snums, thread_id, thread_map):
    """Gets the average wavelengths and powers, updates data_pts."""
    lens = [len(x) for x in switches]
    switches_arr = np.hstack(switches)
    switch_num = -1
    if len(switches_arr):
        switch_num = lens.index(max(lens))
    if thread_map[thread_id]:
        ret = __get_average_data(laser, switch, switches_arr, num_pts, switch_num, pos_used, use_dev, num_snums,
                                 thread_id, thread_map)
        if thread_map[thread_id]:
            return ret
        else:
            return [], []
    else:
        return [], []


def __avg_arr(first, second):
    first = np.array([np.array(x) for x in first])
    second = np.array([np.array(y) for y in second])
    try:
        first += second
        first /= 2
    except ValueError:
        pass
    return first


def __get_data(laser, op_switch, switches_arr, switch_num, pos_used, use_dev, num_snums, num_readings, thread_id,
               thread_map):
    wavelens = [[], [], [], []]
    amps = [[], [], [], []]
    for switch in switches_arr:
        try:
            if use_dev:
                op_switch.set_channel(switch)
            time.sleep(1.2)
            for i in range(num_readings):
                add_wavelen = False
                if not i:
                    add_wavelen = True
                if thread_map[thread_id]:
                    __get_sm125_data(wavelens, amps, switch_num, laser, pos_used, add_wavelen, use_dev, num_snums,
                                     thread_id, thread_map)
        except socket.error:
            pass
    wavelens = [wave for i, wave in enumerate(wavelens) if pos_used[i]]
    amps = [amp for i, amp in enumerate(amps) if pos_used[i]]
    return wavelens, amps


def __get_sm125_data(all_waves, all_amps, switch_num, sm125, pos_used, add_wavelen, use_dev, num_snums, thread_id,
                     thread_map):
    if thread_map[thread_id]:
        wavelens, amps, lens = sm125.get_data(not use_dev, num_snums)
    else:
        return

    try:
        wavelens = list(wavelens)
        amps = list(amps)
    except TypeError:
        wavelens = [wavelens]
        amps = [amps]

    waves_list = []
    amps_list = []
    for i, pos in enumerate(pos_used):
        if pos and lens is not None and lens[i]:
            waves_list.append(wavelens.pop(0))
            amps_list.append(amps.pop(0))
        else:
            waves_list.append(0.)
            amps_list.append(0.)

    first_run = True
    if len(np.hstack(all_waves)):
        first_run = False
    for i, (amp, wave) in enumerate(zip(amps_list, waves_list)):
        if first_run or (i == switch_num and add_wavelen):
            all_waves[i].append(wave)
            all_amps[i].append(amp)
        else:
            temp_wave = all_waves[i].pop()
            temp_amp = all_amps[i].pop()
            all_waves[i].insert(len(all_waves[i]), (temp_wave + wave) / 2.)
            all_amps[i].insert(len(all_amps[i]), (temp_amp + amp) / 2.)


def __get_average_data(laser, op_switch, switches_arr, num_readings, switch_num, pos_used, use_dev, num_snums,
                       thread_id, thread_map):
    all_waves = [[], [], [], []]
    all_amps = [[], [], [], []]
    wavelengths, amplitudes = __get_data(laser, op_switch, switches_arr, switch_num, pos_used, use_dev,
                                         num_snums, num_readings, thread_id, thread_map)
    all_waves = __avg_arr(wavelengths, all_waves)
    all_amps = __avg_arr(amplitudes, all_amps)
    return np.hstack(all_waves), np.hstack(all_amps)
