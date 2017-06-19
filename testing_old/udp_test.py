import socket

UDPSock_send = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

'''mess = bytes.fromhex('AA 55 E0 00 00 00 04 02 11 11 00 FF')
'''

mess = bytes.fromhex('aa 55 e0 0e 00 00 04 02 00 05 03 02 00 20 08 02 00 00 09 02 81 90 01 01 02 00 00 ff')

'''mess = bytes.fromhex('aa 55 e0 0e 00 00 04 02 00 05 03 02 00 20 01 01 02 00 00 ff')
'''
# print(mess)
# data = bytearray([0xAA, 0x55, 0xE0, 0x0E, 0x00, 0x02, 0x04, 0x02, 0x11, 0x11, 0x03, 0x02, 0x11, 0x11, 0x01, 0x01,
#  0x02, 0x00, 0x00, 0xFF])


address = '10.0.0.150'
UDPSock_send.sendto(mess, (address, 30070))

print("Recv")
UDPSock_receive = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
UDPSock_receive.bind(('10.0.0.1', 30070))
data, addr = UDPSock_receive.recvfrom(2048)
print(data)

"""
import socket

UDP_IP_SEND = "10.0.0.150"
UDP_PORT_SEND = 30001
MESSAGE = b'AA55 E00E 0000 0402 0000 0302 0000 0101 0200 00FF'

print("UDP target IP:", UDP_IP_SEND)
print("UDP target port:", UDP_PORT_SEND)
print("message:", MESSAGE)

sock_SEND = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock_SEND.setsockopt(sock_SEND, UDP_IP_SEND, 1)
sock_SEND.sendto(MESSAGE, (UDP_IP_SEND, UDP_PORT_SEND))


UDP_IP_RECV = "127.0.0.1"
UDP_PORT_RECV = 30072


sock_RECV = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock_RECV.setsockopt(sock_RECV, UDP_IP_RECV, 1)
sock_RECV.bind((UDP_IP_RECV, UDP_PORT_RECV)

while True:
    data, addr = sock_RECV.recvfrom(1024)
    print("received message:", data)
"""
