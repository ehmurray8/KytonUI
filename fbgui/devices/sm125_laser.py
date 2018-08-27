import socket
from socket import AF_INET, SOCK_STREAM
from typing import List, Tuple
import struct
from enum import Enum

WAVELENGTH_MULTIPLIER = 10000.0
AMPLITUDE_MULTIPLIER = 100.0


class SM125DataType(Enum):
    WAVELENGTH = (4, 'i', WAVELENGTH_MULTIPLIER)
    AMPLITUDE = (2, 'h', AMPLITUDE_MULTIPLIER)

    def byte_length(self) -> int:
        return self.value[0]

    def type_specifier(self) -> str:
        return self.value[1]

    def multiplier(self) -> float:
        return self.value[2]


class SM125(socket.socket):
    """Socket connection for SM125 device."""
    def __init__(self, address, port):
        socket.setdefaulttimeout(3)
        super().__init__(AF_INET, SOCK_STREAM)
        super().connect((address, port))
        self.response_position = 0
        self.response = b""

    def get_data(self, use_positions: List[bool]) -> Tuple[List[float], List[float]]:
        """
        Returns the SM125 wavelengths, amplitudes, the two lists are both of length 4, a value of 0 is used if no
        peak is detected on a channel that is expecting data, or used if not expecting data on a channel.

        :param use_positions: list of 4 values, True if expecting data on that channel, False otherwise
        :returns: Wavelength readings, Amplitude readings
        """
        self.send(b'#GET_PEAKS_AND_LEVELS')
        response_length = int(self.recv(10))
        self.response = self.recv(response_length)

        self.response_position = 12
        channel_lengths = []
        for _ in range(4):
            start = self.response_position
            self.response_position += 2
            channel_length_bytes = self.response[start:self.response_position]
            channel_length = struct.unpack('H', channel_length_bytes)[0]
            channel_lengths.append(channel_length)

        self.response_position += 12

        wavelengths = self.__parse_values(SM125DataType.WAVELENGTH, channel_lengths, use_positions)
        amplitudes = self.__parse_values(SM125DataType.AMPLITUDE, channel_lengths, use_positions)
        return wavelengths, amplitudes

    def __parse_values(self, sm125_type: SM125DataType, channel_lengths: List[int], use_positions: List[bool]):
        values = []
        for i in range(4):
            for j in range(channel_lengths[i]):
                start = self.response_position
                self.response_position += sm125_type.byte_length()
                value_bytes = self.response[start:self.response_position]
                value = struct.unpack(sm125_type.type_specifier(), value_bytes)[0] / sm125_type.multiplier()
                if j == 0 and use_positions[i]:
                    values.append(value)
            if (use_positions[i] and not channel_lengths[i]) or not use_positions[i]:
                values.append(0.0)
        return values
