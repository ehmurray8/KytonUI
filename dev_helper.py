"""
Gets the amplitude and wavelength data using the Mircon Optics SM125,
and the Optical Switch.
"""
# pylint: disable=import-error, relative-import, superfluous-parens
import asyncio
import socket
import numpy as np
from collections import Iterable


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
            await __get_sm125_data(wavelens, amps, switch_num, laser, pos_used, use_dev, num_snums)
        except socket.error:
            pass
    return wavelens, amps


async def __get_sm125_data(all_waves, all_amps, switch_num, sm125, pos_used, use_dev=True, num_snums=0):
    wavelens, amps, lens = await sm125.get_data(not use_dev, num_snums)
    list(wavelens)
    list(amps)
    pos_used = [x for x in pos_used if x]

    ##
    # TODO Add check to fill in missing readings with 0s using pos_used, and lens
    ##

    #for i, (length, use_pos) in enumerate(zip(lens, pos_used)):
    #    if not length and use_pos:
    #        amps.insert(i, )

    first_run = True
    if len(np.hstack(all_waves)):
        first_run = False
    for i, (amp, wave) in enumerate(zip(list(amps), list(wavelens))):
        if first_run or i == switch_num:
            all_waves[i].append(wave)
            all_amps[i].append(amp)
        else:
            temp_wave = all_waves[i].pop(0)
            temp_amp = all_amps[i].pop(0)
            all_waves[i].insert(0, (temp_wave + wave) / 2.)
            all_amps[i].insert(0, (temp_amp + amp) / 2.)
    print("All waves: {}, All amps: {}".format(all_waves, all_amps))


async def __get_average_data(laser, op_switch, switches_arr, num_readings, switch_num, pos_used, use_dev=True, num_snums=0):
    all_waves = [[], [], [], []]
    all_amps = [[], [], [], []]
    wavelengths, amplitudes = await __get_data(laser, op_switch, switches_arr, switch_num, pos_used, use_dev,
                                               num_snums, num_readings)
    all_waves = __avg_arr(wavelengths, all_waves)
    all_amps = __avg_arr(amplitudes, all_amps)
    return np.hstack(all_waves), np.hstack(all_amps)
