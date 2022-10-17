import socket
import struct

msgFromClient = "Hello UDP Server"
bytesToSend = str.encode(msgFromClient)

serverAddressPort = ("192.168.2.2", 42069)
bufferSize = 1024

UDPClientSocket = socket.socket(family=socket.AF_INET, type=socket.SOCK_DGRAM)

UDPClientSocket.sendto(bytesToSend, serverAddressPort)

msgFromServer = UDPClientSocket.recvfrom(bufferSize)

print("Message from server: ", struct.unpack('f', msgFromServer[0]))