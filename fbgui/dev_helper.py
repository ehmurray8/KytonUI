"""
Gets the amplitude and wavelength data using the Micron Optics SM125, and the Optical Switch.
"""
import socket
import time
import numpy as np
from typing import List, Tuple
from uuid import UUID
from queue import Queue
from fbgui.messages import MessageType, Message
from fbgui.devices.sm125_laser import SM125
from fbgui.devices.optical_switch import OpticalSwitch


class Params(object):
    """Wrapper for the parameters used throughout the module."""

    def __init__(self, laser: SM125, switch: OpticalSwitch, switches: List[int], num_pts: int, pos_used: List[int],
                 num_snums: int, thread_id: UUID, thread_map: dict, main_queue: Queue, switch_num: int):
        """

        :param laser: the SM125 wrapper used for communicating with the SM125
        :param switch: the optical switch wrapper used for communicating with the optical switch
        :param switches: flattened list of switches from the 2D list of switches broken down by channel
        :param num_pts: the number of readings to take for each fbg
        :param pos_used: the number of fbgs on each SM125 channel
        :param num_snums: total number of fbgs in the current test
        :param thread_id: UUID of the thread the code is currently running on
        :param thread_map: Dictionary mapping UUIDs to boolean values corresponding to whether or not the thread with
                           that UUID should be running
        :param main_queue: Queue used for writing log messages to
        :param switch_num: the number of fbgs the program has to switch to using the optical switch
        """
        self.laser = laser
        self.switch = switch
        self.switches = switches
        self.num_readings = num_pts
        self.positions_used = pos_used
        self.num_snums = num_snums
        self.thread_id = thread_id
        self.thread_map = thread_map
        self.main_queue = main_queue
        self.switch_num = switch_num


def avg_waves_amps(laser: SM125, switch: OpticalSwitch, switches: List[List[int]], num_pts: int, pos_used: List[int],
                   num_snums: int, thread_id: UUID, thread_map: dict, main_queue: Queue)\
        -> Tuple[List[float], List[float]]:
    """
    Returns the averaged wavelength, and power data collected from the SM125, and potentially using the Optical Switch.
    The data is collected num_pts amount of times and then averaged. The wavelengths and power data are returned
    in order of the serial numbers, and corresponding indices match between the two lists.


    :param laser: the SM125 wrapper used for communicating with the SM125
    :param switch: the optical switch wrapper used for communicating with the optical switch
    :param switches: 2D list with one list for each SM125 channel containing the switch positions on each channel
    :param num_pts: the number of readings to take for each fbg
    :param pos_used: the number of fbgs on each SM125 channel
    :param num_snums: total number of fbgs in the current test
    :param thread_id: UUID of the thread the code is currently running on
    :param thread_map: Dictionary mapping UUIDs to boolean values corresponding to whether or not the thread with that
                       UUID should be running
    :param main_queue: Queue used for writing log messages to
    """
    lens = [len(x) for x in switches]
    switches_flat = list(np.hstack(switches))
    switch_num = -1
    if len(switches_flat):
        switch_num = lens.index(max(lens))
    if thread_map[thread_id]:
        params = Params(laser, switch, switches_flat, num_pts, pos_used, num_snums,
                        thread_id, thread_map, main_queue, switch_num)
        ret = __get_average_data(params)
        if thread_map[thread_id]:
            return ret
        else:
            return [], []
    else:
        return [], []


def __avg_arr(first: List[List[float]], second: List[List[float]]) -> np.array:
    """
    Averages the values of two matrices, keeps the same shape when returned.

    :param first: first matrix
    :param second: second matrix
    :return: returns average of the two matrices, if there is a ValueError returns the first matrix as np array
    """
    first = np.array([np.array(x) for x in first])
    second = np.array([np.array(y) for y in second])
    try:
        first += second
        first /= 2
    except ValueError:
        pass
    return first


def __get_data(params: Params) -> Tuple[List[List[float]], List[List[float]]]:
    """
    Get the data from the laser, and use the optical switch to configure the fbgs correctly.

    :param params: Params object describing data collection parameters
    :return: Matrix of wavelengths, Matrix of powers
    """
    wavelengths = [[], [], [], []]
    amplitudes = [[], [], [], []]
    if len(params.switches) == 0:
        record_wavelengths_and_amplitudes(wavelengths, amplitudes, params)
    for position_number in params.switches:
        try:
            __switch_to(position_number, params)
            record_wavelengths_and_amplitudes(wavelengths, amplitudes, params)
        except socket.error:
            params.main_queue.put(Message(MessageType.DEVELOPER, "Socket Error", "Error communicating with the "
                                                                                 "laser in dev_helper."))
    wavelengths = [wave for i, wave in enumerate(wavelengths) if params.positions_used[i]]
    amps = [amp for i, amp in enumerate(amplitudes) if params.positions_used[i]]
    return wavelengths, amps


def record_wavelengths_and_amplitudes(wavelengths: List[List[float]], amplitudes: List[List[float]], params: Params):
    for reading_number in range(params.num_readings):
        add_wavelength = not bool(reading_number)
        if params.thread_map[params.thread_id]:
            __get_sm125_data(wavelengths, amplitudes, add_wavelength, params)


def __switch_to(position: int, params: Params):
    params.switch.set_channel(position)
    time.sleep(1.2)


def __get_sm125_data(all_waves: List[List[float]], all_amps: List[List[float]], add_wavelength: bool, params: Params):
    """
    Collect the data from the SM125, and add the data to the proper lists in all_waves, and all_amps.

    :param all_waves: Matrix of all wavelengths, with a list for each sm125 channel, updated in this function
    :param all_amps: Matrix of all powers, with a list for each sm125 channel, updated in this function
    :param add_wavelength: if True add the wavelength and power points to the end of the channel list, otherwise,
                           average the points with the last point in the channel list
    :param params: data collection parameters object
    """
    if params.thread_map[params.thread_id]:
        use_positions = [bool(num_on_position) for num_on_position in params.positions_used]
        wavelengths, amplitudes = params.laser.get_data(use_positions)

        first_run = True
        if len(np.hstack(all_waves)):
            first_run = False
        for i, (amplitude, wavelength, use_position) in enumerate(zip(amplitudes, wavelengths, use_positions)):
            if use_position:
                if first_run or (i == params.switch_num and add_wavelength):
                    all_waves[i].append(wavelength)
                    all_amps[i].append(amplitude)
                else:
                    current_wavelength = all_waves[i].pop()
                    current_amplitude = all_amps[i].pop()
                    all_waves[i].insert(len(all_waves[i]), (current_wavelength + wavelength) / 2.)
                    all_amps[i].insert(len(all_amps[i]), (current_amplitude + amplitude) / 2.)


def __get_average_data(params: Params) -> Tuple[List[float], List[float]]:
    """
    Returns the averaged wavelengths and powers using the params object to configure the readings.

    :param params: data collection parameters
    :returns list of wavelengths, list of amplitudes
    """
    all_waves = [[], [], [], []]
    all_amps = [[], [], [], []]
    wavelengths, amplitudes = __get_data(params)
    all_waves = __avg_arr(wavelengths, all_waves)
    all_amps = __avg_arr(amplitudes, all_amps)
    return list(np.hstack(all_waves)), list(np.hstack(all_amps))
