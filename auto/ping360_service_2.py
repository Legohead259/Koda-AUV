from ctypes import sizeof
from brping import Ping360
import numpy as np
import time
import socket
import struct
import csv

# Ping initialization
ping360 = Ping360()
#myPing.connect_serial("COM4", 115200)
# For UDP

ping360.connect_udp("192.168.2.182", 12345)

if ping360.initialize() is False:
    print("Failed to initialize Ping!")
    exit(1)

# Server intialization
localIP = "0.0.0.0"
localPort = 42069
bufferSize = 1024

udp_server_socket = socket.socket(family=socket.AF_INET, type=socket.SOCK_DGRAM) # Create datagram socket
udp_server_socket.bind((localIP, localPort)) # Bind to address and port

# ==========================
# === CONFIGURATION DATA ===
# ==========================

# set the speed of sound to use for distance calculations to
# 1450000 mm/s (1450 m/s)
# ping360.set_speed_of_sound(1450000)

# =========================
# === SERVICE FUNCTIONS ===
# =========================

def meters_per_sample(ping_message, v_sound=1480):
    """ Returns the target distance per sample, in meters. 
    
    @param: 'ping_message' is the message being analysed.
    @param: 'v_sound' is the operating speed of sound [m/s]. Default 1500.

    """
    # sample_period is in 25ns increments
    # time of flight includes there and back, so divide by 2
    return v_sound * ping_message.sample_period * 12.5e-9

# ====================
# === SERVICE LOOP ===
# ====================

while True:
    # Listen for incoming datagrams
    bytesAddressPair = udp_server_socket.recvfrom(bufferSize)
    message = bytesAddressPair[0]
    client_address = bytesAddressPair[1]

    # Get data from the Ping360
    data = ping360.transmitAngle(300) # 300 right
    # distance per sample
    mps = meters_per_sample(data)

    # Initializing lists
    Distances = []
    Intensity = []

    # Computing distances and intensities of the different samples
    for i in range(len(data.msg_data)):
        Distances.append(i * mps)
        Intensity.append(data.msg_data[i])

    # Create a CSV file of distances and intensities
    with open('Intensities13.csv', 'w') as file:
        writer = csv.writer(file)
        for i in range(len(Distances)):
            writer.writerow([Distances[i], Intensity[i]])

    # Converting lists to arrays
    Array_Distances = np.array(Distances)
    Array_Intensity = np.array(Intensity)

    # Below 0.75m reject all samples
    Limit = 0.75

    ## Finding the index of the 0.75m distance

        # calculate the difference array
    difference_array = np.absolute(Array_Distances - Limit)

        # find the index of minimum element from the array
    index_Limit = difference_array.argmin()

    # Set all intensity values at a distance below 0.75m to zero
    for i in range(index_Limit):
        Array_Intensity[i] = 0.0

    # Find index of the true maximum return
    index_max = Array_Intensity.argmax()

    # Store intensity and distance of strongest return
    Intensity_max_return = Array_Intensity[index_max]
    Distance_max_return = Array_Distances[index_max]

    print(Intensity_max_return)
    print(Distance_max_return)

    udp_server_socket.sendto(bytearray(struct.pack("f",  Distance_max_return)), client_address)
    
