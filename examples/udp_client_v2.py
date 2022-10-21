import socket
import struct
import pickle as pk

serverAddressPort = ("192.168.2.2", 42069)
bufferSize = 2048

UDPClientSocket = socket.socket(family=socket.AF_INET, type=socket.SOCK_DGRAM)

# Configuration of sonar
toserver = {
    'Number of samples' : 10,
    'Angle' : 200,
    "Enable Logging" : True,
    "Range" : 5, # Range SONAR should scan [m]
    "Readings": 1200 # Number of readings Ping360 should take
}

# Sending sonar configuration to server
UDPClientSocket.sendto(pk.dumps(toserver), serverAddressPort)

# Loading the data sent by the server
msgFromServer = pk.loads(UDPClientSocket.recv(bufferSize))

# Reading the dictionary sent by the server
distance = msgFromServer[0]
intensity = msgFromServer[1]

print(distance)
print(intensity)