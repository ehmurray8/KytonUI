import socket
from socket import AF_INET, SOCK_STREAM


class OpticalSwitch(socket.socket):
    """Object representation of the Optical Switch needed for the program, overrides the socket module."""

    def __init__(self, address, port, use_dev):
        """
        Connects to the specified address, and port using a socket connection.

        :param address: IP address of the optical switch
        :param port: Port of the optical switch
        :param use_dev: If true connect to the device
        """
        socket.setdefaulttimeout(3)
        if use_dev:
            super().__init__(AF_INET, SOCK_STREAM)
            super().connect((address, port))

    def set_channel(self, channel: int):
        """
        Sets the channel on the optical switch.

        :param channel: channel to set the optical switch to
        """
        message = "<OSW{}_OUT_{}>".format(format(int(1), '02d'), format(int(channel), '02d'))
        self.send(message.encode())
