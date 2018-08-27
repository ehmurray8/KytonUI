from socket import AF_INET, SOCK_STREAM, socket
from typing import List, Tuple
import struct


def create_socket() -> socket:
    sock = socket(AF_INET, SOCK_STREAM)
    sock.connect(('127.0.0.1', 1853))
    return sock


def get_channel_data(sock: socket) -> Tuple[float, float, List[float]]:
    wavelength_start = sock.recv(8)
    wavelength_start = struct.unpack('d', wavelength_start)[0]

    wavelength_step = sock.recv(8)
    wavelength_step = struct.unpack('d', wavelength_step)[0]

    number_points = sock.recv(4)
    number_points = struct.unpack('I', number_points)[0]

    print("Start: {}, Step: {}, Number of points: {}".format(wavelength_start, wavelength_step, number_points))

    channel_amplitudes = []
    for _ in range(number_points):
        amplitude = sock.recv(8)
        amplitude = struct.unpack('d', amplitude)[0]
        channel_amplitudes.append(amplitude)

    return wavelength_start, wavelength_step, channel_amplitudes


if __name__ == "__main__":
    SOCK = create_socket()
    SOCK.send(b"#GET_FULLSPECTRUM\n")
    response_length = SOCK.recv(4)
    response_length = struct.unpack('I', response_length)[0]

    response_type = SOCK.recv(1)
    response_type = struct.unpack('B', response_type)[0]

    response_status = SOCK.recv(1)
    response_status = struct.unpack('B', response_status)[0]

    print("Length: {}, Type: {}, Status: {}".format(response_length, response_type, response_status))

    channel_info = []
    for i in range(4):
        channel_data = get_channel_data(SOCK)
        amplitude_max = max(channel_data[2])
        print("Channel {} max: {}".format(i+1, amplitude_max))
        channel_info.append(channel_data)

    SOCK.close()
