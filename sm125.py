"""Module used to interface with Micron Options SM125 device."""

import socket
from socket import AF_INET, SOCK_STREAM
import numpy as np

WAVELEN_SCALE_FACTOR = 10000.0
AMP_SCALE_FACTOR = 100.0


class SM125(socket.socket):
    """TCP socket connection for SM125 device."""
    def __init__(self, address, port):
        super().__init__(AF_INET, SOCK_STREAM)
        super().connect((address, port))

    def get_data(self):
        """Returns the SM125 wavelengths, amplitudes, and lengths of each channel."""
        self.send(b'#GET_PEAKS_AND_LEVELS')
        pre_response = self.recv(10)
        response = self.recv(int(pre_response))
        response = np.fromstring(response[:20], dtype='3uint32, 4uint16')

        chan_lens = response[0][1]
        total_peaks = sum(chan_lens)

        wave_start_idx = 32
        wave_end_idx = wave_start_idx + 4 * total_peaks
        wavelengths = np.fromstring(response[wave_start_idx:wave_end_idx],
                                    dtype=(str(total_peaks) + 'int32'))
        amp_start_idx = wave_end_idx
        amp_end_idx = amp_start_idx + 2 * total_peaks
        amplitudes = np.fromstring(response
                                   [amp_start_idx:amp_end_idx],
                                   dtype=(str(total_peaks) + 'int16'))

        wavelengths_list = [en / WAVELEN_SCALE_FACTOR for en in wavelengths]
        amplitudes_list = [en / AMP_SCALE_FACTOR for en in amplitudes]

        return wavelengths_list[0], amplitudes_list[0], chan_lens
