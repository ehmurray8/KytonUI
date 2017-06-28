import socket

import numpy

UDPSock_send = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

mess = bytes.fromhex('aa 55 e0 0e 00 00 04 02 00 05 03 02 00 20 08 02 00 00 09 02 81 90 01 01 02 00 00 ff')

address = '10.0.0.150'
UDPSock_send.sendto(mess, (address, 30070))

print("Recv")
UDPSock_receive = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
UDPSock_receive.bind(('10.0.0.1', 30002))
data, addr = UDPSock_receive.recvfrom(21930)

data_fr = numpy.fromstring(data[:36], dtype='uint16, 2uint8, 4uint32, 4uint16, 2uint32')
data_fr2 = numpy.fromstring(data[36:], dtype='uint16', count=10)

print(data_fr)
print(data_fr2)
