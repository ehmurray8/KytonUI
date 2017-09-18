import socket
from socket import AF_INET, SOCK_STREAM, socket

def setup(addr, port):
    soc = socket(AF_INET, SOCK_STREAM)
    soc.connect((addr, port))
    return soc

def set_channel(op_switch, addr, chan):
    msg = "<OSW{}_OUT_{}>".format(format(int(addr), '02d'), format(int(chan), '02d'))
    soc.send(msg.encode(msg))
