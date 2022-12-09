import socket
import struct
import pickle as pk

serverAddressPort = ("192.168.2.2", 42069)
bufferSize = 4096

UDPClientSocket = socket.socket(family=socket.AF_INET, type=socket.SOCK_DGRAM)

# Configuration of sonar
toserver = {
    'n_samples': 200,
    'angle' : 300, #300 Starboard 100 port
    "log_en" : True,
    "range" : 5, # Range SONAR should scan [m]
    "readings": 1200 # Number of readings Ping360 should take
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