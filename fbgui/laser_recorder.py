"""
Gets the amplitude and wavelength data using the Micron Optics SM125, and the Optical Switch.
"""
import socket
import time
from queue import Queue
from typing import List, Tuple
from uuid import UUID

import numpy as np

from fbgui.devices.optical_switch import OpticalSwitch
from fbgui.devices.sm125_laser import SM125
from fbgui.exceptions import ProgramStopped
from fbgui.laser_data import LaserData
from fbgui.messages import MessageType, Message


class LaserRecorder:
    def __init__(self, laser: SM125, switch: OpticalSwitch, switches: List[List[int]], num_pts: int,
                 thread_id: UUID, thread_map: dict, main_queue: Queue):
        """
        Returns the averaged wavelength, and power data collected from the SM125, and potentially using the
        Optical Switch. The data is collected num_pts amount of times and then averaged. The wavelengths and power
        data are returned in order of the serial numbers, and corresponding indices match between the two lists.


        :param laser: the SM125 wrapper used for communicating with the SM125
        :param switch: the optical switch wrapper used for communicating with the optical switch
        :param switches: 2D list with one list for each SM125 channel containing the switch positions on each channel
        :param num_pts: the number of readings to take for each fbg
        :param thread_id: UUID of the thread the code is currently running on
        :param thread_map: Dictionary mapping UUIDs to boolean values corresponding to whether or not the
                    thread with that UUID should be running
        :param main_queue: Queue used for writing log messages to
        """
        self.laser = laser
        self.optical_switch = switch
        self.switch_positions = switches
        self.number_of_readings = num_pts
        self.thread_id = thread_id
        self.thread_map = thread_map
        self.main_queue = main_queue
        lens = [len(x) for x in filter(lambda x: x != 0, switches)]
        self.switch_channel_index = lens.index(max(lens))

    def get_wavelength_amplitude_data(self) -> Tuple[List[float], List[float]]:
        if self.thread_map[self.thread_id]:
            try:
                wavelengths, amplitudes = self.__get_data()
                return list(np.hstack(wavelengths)), list(np.hstack(amplitudes))
            except ProgramStopped:
                pass
        return [], []

    def __get_data(self) -> Tuple[List[List[float]], List[List[float]]]:
        """
        Get the data from the laser, and use the optical switch to configure the fbgs correctly.

        :return: Matrix of wavelengths, Matrix of powers
        """
        laser_data = LaserData(self.switch_positions, self.switch_channel_index)
        if len(self.switch_positions) == 0:
            self.record_wavelengths_and_amplitudes(laser_data, 0)
        switch_set = set(self.switch_positions[self.switch_channel_index])
        for switch_position in sorted(switch_set):
            try:
                if switch_position != 0:
                    self.__switch_to(switch_position)
                self.record_wavelengths_and_amplitudes(laser_data, switch_position)
            except socket.error:
                self.main_queue.put(Message(MessageType.DEVELOPER, "Socket Error", "Error communicating with the "
                                                                                   "laser in dev_helper."))
        return laser_data.get_wavelengths(), laser_data.get_powers()

    def __switch_to(self, position: int):
        self.optical_switch.set_channel(position)
        time.sleep(1.2)

    def record_wavelengths_and_amplitudes(self, laser_data: LaserData, switch_position: int):
        for reading_number in range(self.number_of_readings):
            wavelengths, powers = self.__get_sm125_data()
            for channel in range(4):
                if len(self.switch_positions[channel]):
                    laser_data.add_wavelengths(channel, wavelengths[channel], switch_position)
                    laser_data.add_powers(channel, powers[channel], switch_position)

    def __get_sm125_data(self):
        """Collect the data from the SM125, and add the data to the proper lists in all_waves, and all_amps."""
        if self.thread_map[self.thread_id]:
            use_positions = [bool(len(channel_positions)) for channel_positions in self.switch_positions]
            return self.laser.get_data(use_positions)
        raise ProgramStopped
