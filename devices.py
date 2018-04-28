"""Contains object representations of all the necessary devices."""

import socket
from socket import AF_INET, SOCK_STREAM
import numpy as np
import random

WAVELEN_SCALE_FACTOR = 10000.0
AMP_SCALE_FACTOR = 100.0


class SM125(socket.socket):
    """TCP socket connection for SM125 device."""
    def __init__(self, address, port, use_dev):
        socket.setdefaulttimeout(3)
        super().__init__(AF_INET, SOCK_STREAM)
        if use_dev:
            super().connect((address, port))

    def get_data(self, dummy_value=False, num=0):
        """Returns the SM125 wavelengths, amplitudes, and lengths of each channel."""
        if dummy_value:
            waves = []
            amps = []
            wave_start_num = 0
            wave_end_num = 25
            amp_start_num = 0
            amp_end_num = -.5
            for _ in range(num-1):
                waves.append(random.uniform(1500+wave_start_num, 1500 + wave_end_num))
                wave_start_num += 25
                wave_end_num += 25
                amps.append(random.uniform(-10+amp_start_num, -10 + amp_end_num))
                amp_start_num += .25
                amp_end_num += .25
            return waves, amps, None
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


class Oven(object):
    """Delta oven object, uses pyvisa."""
    def __init__(self, port, manager, use_dev):
        self.device = None
        loc = "GPIB0::{}::INSTR".format(port)
        if use_dev:
            self.device = manager.open_resource(loc, read_termination="\n", open_timeout=2500)

    def set_temp(self, temp):
        """Sets set point of delta oven."""
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
        self.device.close()


class OpSwitch(socket.socket):
    """Object representation of the Optical Switch needed for the program."""

    def __init__(self, addr, port, use_dev):
        socket.setdefaulttimeout(3)
        super().__init__(AF_INET, SOCK_STREAM)
        if use_dev:
            super().connect((addr, port))

    def set_channel(self, chan):
        """Sets the channel on the optical switch."""
        msg = "<OSW{}_OUT_{}>".format(format(int(1), '02d'), format(int(chan), '02d'))
        self.send(msg.encode())


class TempController(object):
    """Object representation of the Temperature Controller needed for the program."""
    def __init__(self, port, manager, use_dev):
        self.device = None
        loc = "GPIB0::{}::INSTR".format(port)
        if use_dev:
            self.device = manager.open_resource(loc, read_termination='\n', open_timeout=2500)

    def get_temp_c(self):
        """Return temperature reading in degrees C."""
        query = self.device.query('CRDG? B')
        return query[:-4]

    def get_temp_k(self, dummy_val=False, center_num=0):
        """Return temperature reading in degrees Kelvin."""
        if dummy_val:
            return float(random.gauss(center_num - 5, center_num + 5))
        else:
            query = self.device.query('KRDG? B')
            return float(query[:-4])

    def close(self):
        """Close the device connection."""
        self.device.close()
