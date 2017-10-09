import socket
from socket import AF_INET, SOCK_STREAM


class OpSwitch(socket.socket):

    def __init__(self, addr, port):
        super().__init__(AF_INET, SOCK_STREAM)
        self.connect((addr, port))

    def set_channel(self, addr, chan):
        msg = "<OSW{}_OUT_{}>".format(format(int(addr), '02d'), format(int(chan), '02d'))
        self.send(msg.encode())
