import socket
from socket import AF_INET, SOCK_STREAM
from typing import List, Tuple
import numpy as np

WAVELENGTH_MULTIPLIER = 10000.0
AMPLITUDE_MULTIPLIER = 100.0


class SM125(socket.socket):
    """UDP socket connection for SM125 device."""
    def __init__(self, address, port):
        socket.setdefaulttimeout(3)
        super().__init__(AF_INET, SOCK_STREAM)
        super().connect((address, port))

    def get_data(self) -> Tuple[List[float], List[float], List[float]]:
        """
        Returns the SM125 wavelengths, amplitudes, and number of elements recorded for each channel.

        :returns: Wavelength readings, Amplitude readings, Number of readings on each channel, if using fake values then
                  the third parameter is empty
        """
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

        wavelengths_list = [en / WAVELENGTH_MULTIPLIER for en in wavelengths]
        amplitudes_list = [en / AMPLITUDE_MULTIPLIER for en in amplitudes]
        return wavelengths_list[0], amplitudes_list[0], chan_lens
