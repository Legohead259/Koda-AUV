import socket

msgFromClient = "Hello UDP Server"
bytesToSend = str.encode(msgFromClient)
serverAddressPort = ("0.0.0.0", 20001)
bufferSize = 1024

UDPClientSocket = socket.socket(family=AF_INET, type=socket.SOCK_DGRAM)

UDPClientSocket.sendTo(bytesToSend, serverAddressPort)

msgFromServer = UDPClientSocket.recvfrom(bufferSize)

print("Message from server: ", msgFromServer)