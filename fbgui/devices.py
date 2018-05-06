"""Contains object representations of all the necessary devices."""

import socket
from socket import AF_INET, SOCK_STREAM
import numpy as np
import random
from typing import List, Tuple
from visa import ResourceManager

# SM125 Data Constants
WAVELEN_SCALE_FACTOR = 10000.0
AMP_SCALE_FACTOR = 100.0


class SM125(socket.socket):
    """UDP socket connection for SM125 device."""
    def __init__(self, address, port, use_dev):
        socket.setdefaulttimeout(3)
        super().__init__(AF_INET, SOCK_STREAM)
        if use_dev:
            super().connect((address, port))

    def get_data(self, dummy_value=False, num=0) -> Tuple[List[float], List[float], List[float]]:
        """
        Returns the SM125 wavelengths, amplitudes, and number of elements recorded for each channel.

        :param dummy_value: If true then make up fake values, otherwise query the SM125 for wavelength and power data
        :param num: number of fake values to make up
        :returns: Wavelength readings, Amplitude readings, Number of readings on each channel, if using fake values then
                  the third parameter is empty
        """
        if dummy_value:
            waves = []
            amps = []
            wave_start_num = 0
            wave_end_num = 25
            amp_start_num = 0
            amp_end_num = -.5
            for _ in range(num):
                waves.append(random.uniform(1500+wave_start_num, 1500 + wave_end_num))
                wave_start_num += 25
                wave_end_num += 25
                amps.append(random.uniform(-10+amp_start_num, -10 + amp_end_num))
                amp_start_num += .25
                amp_end_num += .25
            return waves, amps, []
        else:
            self.send(b'#GET_PEAKS_AND_LEVELS')
            pre_response = self.recv(10)
            response = self.recv(int(pre_response))
            chan_lens = np.frombuffer(response[:20], dtype='3uint32, 4uint16')[0][1]
            total_peaks = sum(chan_lens)

            wave_start_idx = 32
            wave_end_idx = wave_start_idx + 4 * total_peaks
            wavelengths = np.frombuffer(response[wave_start_idx:wave_end_idx], dtype=(str(total_peaks) + 'int32'))
            amp_start_idx = wave_end_idx
            amp_end_idx = amp_start_idx + 2 * total_peaks
            amplitudes = np.frombuffer(response[amp_start_idx:amp_end_idx], dtype=(str(total_peaks) + 'int16'))

            wavelengths_list = [en / WAVELEN_SCALE_FACTOR for en in wavelengths]
            amplitudes_list = [en / AMP_SCALE_FACTOR for en in amplitudes]
            return wavelengths_list[0], amplitudes_list[0], chan_lens


class Vidia(object):
    """
    Vidia-Swept laser wrapper object.

    :ivar Resource device: PyVisa GPIB connection to the device
    """

    def __init__(self, loc: str, manager: ResourceManager, use_dev: bool):
        """
        Create a visa connection using loc and manager to the Vidia-Swept laser.

        :param loc: the GPIB location of the laser
        :param manager:  the PyVisa resource manager
        :param use_dev: if True connect to laser
        """
        self.device = None
        if use_dev:
            self.device = manager.open_resource(loc)

    def start_scan(self):
        """Starts the scanning process for the laser."""
        self.device.query(":OUTP ON")
        self.device.query(":OUTP:TRAC OFF")
        self.device.query(":OUTP:SCAN:STAR -1")

    def wave_info(self):
        """Returns wavelength information from the laser."""
        return self.device.query(":WAVE MIN?"), self.device.query(":WAVE?"), self.device.query(":WAVE MAX?")


class Oven(object):
    """
    Delta oven object, uses pyvisa.

    :ivar Resource device: PyVisa GPIB connection to the device
    """

    def __init__(self, loc: str, manager: ResourceManager, use_dev: bool):
        """
        Opens a GPIB connection with the device at the specified location.

        :param loc: the location of the device
        :param manager: the PyVisa Resource Manager
        :param use_dev: if True connect to the device
        """
        self.device = None
        if use_dev:
            self.device = manager.open_resource(loc, read_termination="\n", open_timeout=2500)

    def set_temp(self, temp: float):
        """
        Sets set point of delta oven.

        :param temp: Temperature to set the oven to
        """
        self.device.query('S {}'.format(temp))

    def heater_on(self):
        """Turns oven heater on."""
        self.device.query('H ON')

    def heater_off(self):
        """Turns oven heater off."""
        self.device.query('H OFF')

    def cooling_on(self):
        """Turns oven cooling on."""
        self.device.query('C ON')

    def cooling_off(self):
        """Turns oven cooling off."""
        self.device.query('C OFF')

    def close(self):
        """Closes the resource."""
        if self.device is not None:
            self.device.close()


class OpSwitch(socket.socket):
    """Object representation of the Optical Switch needed for the program, overrides the socket module."""

    def __init__(self, addr, port, use_dev):
        """
        Connects to the specified address, and port using a socket connection.

        :param addr: IP address of the optical switch
        :param port: Port of the optical switch
        :param use_dev: If true connect to the device
        """
        socket.setdefaulttimeout(3)
        if use_dev:
            super().__init__(AF_INET, SOCK_STREAM)
            super().connect((addr, port))

    def set_channel(self, chan: int):
        """
        Sets the channel on the optical switch.

        :param chan: channel to set the optical switch to
        """
        msg = "<OSW{}_OUT_{}>".format(format(int(1), '02d'), format(int(chan), '02d'))
        self.send(msg.encode())


class TempController(object):
    """
    Object representation of the Temperature Controller needed for the program.

    :ivar Resource device: PyVisa GPIB connection to the device.
    """
    def __init__(self, loc, manager, use_dev):
        """
        Establishes a GPIB connection with the temperature controller.

        :param loc: the location of the instrument
        :param manager: the PyVisa resource manager
        :param use_dev: if True connect to the device
        """
        self.device = None
        if use_dev:
            self.device = manager.open_resource(loc, read_termination='\n', open_timeout=2500)

    def get_temp_k(self, dummy_val=False, center_num=0):
        """
        Return temperature reading in degrees Kelvin.

        :param dummy_val: If true make up a temperature
        :param center_num: The number the temperature is set to used for simulating the temp reading
        """
        if dummy_val:
            return float(random.gauss(center_num - 5, center_num + 5))
        else:
            query = self.device.query('KRDG? B')
            return float(query[:-4])

    def close(self):
        """Close the device connection."""
        if self.device is not None:
            self.device.close()
