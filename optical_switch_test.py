import socket
from socket import AF_INET, SOCK_STREAM, socket

soc = socket(AF_INET, SOCK_STREAM)

soc.connect(("192.168.1.111", 5000))

print("Input an optical switch command: ")
msg = input()
while msg != "stop":
    soc.send(msg.encode())
    char = soc.recv(1)
    resp = ""
    resp = char
    while char != b'>':
        char = soc.recv(1)
        resp += char
    print(resp)
    print("Next command: ")
    msg = input()
