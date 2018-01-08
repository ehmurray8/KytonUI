"""
Gets the amplitude and wavelength data using the Mircon Optics SM125,
and the Optical Switch.
"""
# pylint: disable=import-error, relative-import, superfluous-parens
import asyncio
import socket
import helpers as help


async def avg_waves_amps(laser, switch, switches, num_pts):
    """Gets the average wavelengths and powers, updates data_pts."""
    lens = [len(x) for x in switches]
    switches_arr = help.flatten(switches)
    switch_num = -1
    if len(switches_arr):
        switch_num = lens.index(max(lens))
    print("beginning dev_help")
    return await __get_average_data(laser, switch, switches_arr, num_pts, switch_num)


def __avg_arr(first, second):
    if len(help.flatten(second)):
        for i, row in enumerate(second):
            for j, col in enumerate(row):
                first[i][j] += col
                first[i][j] /= 2
    return first


async def __get_data(laser, op_switch, switches_arr, switch_num):
    wavelens = [[], [], [], []]
    amps = [[], [], [], []]
    for switch in switches_arr:
        try:
            await op_switch.set_channel(switch)
            await asyncio.sleep(1.2)
            await __get_sm125_data(wavelens, amps, switch_num, laser)
        except socket.error:
            pass
        print(wavelens, amps)
    return wavelens, amps


async def __get_sm125_data(all_waves, all_amps, switch_num, sm125):
    wavelens, amps, lens = await sm125.get_data()
    print("Wavelengths: {}".format(wavelens))
    print("Amplitudes: {}".format(amps))
    print("Lengths: {}".format(lens))
    first_run = True
    if len(help.flatten(all_waves)):
        first_run = False
    for i, (amp, wave) in enumerate(zip(amps, wavelens)):
        if first_run or i == switch_num:
            all_waves[i].append(wave)
            all_amps[i].append(amp)
        else:
            temp_wave = all_waves[i].pop(0)
            temp_amp = all_amps[i].pop(0)
            all_waves[i].insert(0, (temp_wave + wave) / 2.)
            all_amps[i].insert(0, (temp_amp + amp) / 2.)


async def __get_average_data(laser, op_switch, switches_arr, num_readings, switch_num):
    all_waves = [[], [], [], []]
    all_amps = [[], [], [], []]
    for _ in range(num_readings):
        print("Averge data iteration")
        await asyncio.sleep(1.25)
        wavelengths, amplitudes = await __get_data(laser, op_switch, switches_arr, switch_num)
        all_waves = __avg_arr(wavelengths, all_waves)
        all_amps = __avg_arr(amplitudes, all_amps)
    return help.flatten(all_waves), help.flatten(all_amps)
