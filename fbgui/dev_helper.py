"""
Gets the amplitude and wavelength data using the Mircon Optics SM125,
and the Optical Switch.
"""
import asyncio
import socket
import numpy as np


async def avg_waves_amps(laser, switch, switches, num_pts, pos_used, use_dev=True, num_snums=0):
    """Gets the average wavelengths and powers, updates data_pts."""
    lens = [len(x) for x in switches]
    switches_arr = np.hstack(switches)
    switch_num = -1
    if len(switches_arr):
        switch_num = lens.index(max(lens))
    return await __get_average_data(laser, switch, switches_arr, num_pts, switch_num, pos_used, use_dev, num_snums)


def __avg_arr(first, second):
    first = np.array([np.array(x) for x in first])
    second = np.array([np.array(y) for y in second])
    try:
        first += second
        first /= 2
    except ValueError:
        pass
    return first


async def __get_data(laser, op_switch, switches_arr, switch_num, pos_used, use_dev=True, num_snums=0, num_readings=0):
    wavelens = [[], [], [], []]
    amps = [[], [], [], []]
    for switch in switches_arr:
        try:
            if use_dev:
                await op_switch.set_channel(switch)
            await asyncio.sleep(1.2)
            for i in range(num_readings):
                add_wavelen = False
                if not i:
                    add_wavelen = True
                await __get_sm125_data(wavelens, amps, switch_num, laser, pos_used, add_wavelen, use_dev, num_snums)
        except socket.error:
            print("Socket error")
            pass
    wavelens = [wave for i, wave in enumerate(wavelens) if pos_used[i]]
    amps = [amp for i, amp in enumerate(amps) if pos_used[i]]
    return wavelens, amps


async def __get_sm125_data(all_waves, all_amps, switch_num, sm125, pos_used, add_wavelen, use_dev=True, num_snums=0):
    wavelens, amps, lens = await sm125.get_data(not use_dev, num_snums)
    try:
        wavelens = list(wavelens)
        amps = list(amps)
    except TypeError:
        wavelens = [wavelens]
        amps = [amps]

    waves_list = []
    amps_list = []
    for i, pos in enumerate(pos_used):
        if pos and lens[i]:
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


async def __get_average_data(laser, op_switch, switches_arr, num_readings, switch_num, pos_used, use_dev=True, num_snums=0):
    all_waves = [[], [], [], []]
    all_amps = [[], [], [], []]
    wavelengths, amplitudes = await __get_data(laser, op_switch, switches_arr, switch_num, pos_used, use_dev,
                                               num_snums, num_readings)
    all_waves = __avg_arr(wavelengths, all_waves)
    all_amps = __avg_arr(amplitudes, all_amps)
    return np.hstack(all_waves), np.hstack(all_amps)
