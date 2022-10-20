#!/usr/bin/env python

"""
ping360_service.py: This script starts a local server that connects to the Ping360 on the AUV and handles gathering data from it.
This script is intended to run locally on the Raspberry Pi onboard the AUV and access the Ping 360 over a UDP connection.

Client scripts can open a UDP connection to this service's port and the server will command the Ping 360 to begin gathering data along a heading. This service will then filter and parse the data such that the strongest return signal and distance from the AUV is returned to the client. The client may re-connect to the server as many times as desired and receive data.

Note: On start-up there may be a slight delay between client connection and server data sent as the Ping360 SONAR head has to rotated around to the specified bearing. This delay will also be present if different services are trying to work with the Ping 360 such as Ping Viewer. Therefore, it is **not** advised that this service runs consecutively with the Blue Robotics Ping Viewer application.

CHANGELOG:
 - Version 1.0.0: Initial release

TODO:
 - Remove CSV logging features
 - Figure out how to properly filter max intensity accounting for reverb in signal
 - All client to configure certain parameters
    - Angle of scanning
    - Any Ping 360 parameters (e.g. range)
    - If it wants the max intensity+location, min intensity+location, or all intensities+locations
    - Minimum and maximum read distances
 - Add CLI argument parser for Ping 360 Serial (with port) or UDP (with IP address and port)
 -  
"""

__author__      = "Braidan Duffy, Humberto Lebron-Rivera, Omar Jebari, and Erbene de Castro Maia Junior"
__copyright__   = "Copyright 2022"
__credits__     = ["Braidan Duffy", "Humberto Lebron-Rivera", "Omar Jebari", "Erbene de Castro Maia Junior"]
__license__     = "MIT"
__version__     = "1.0.0"
__maintainer__  = "Braidan Duffy"
__email__       = "bduffy2018@my.fit.edu"
__status__      = "Development"

from brping import Ping360
import numpy as np
import socket
import struct
import csv

# Ping initialization
ping360 = Ping360()
ping360.connect_udp("192.168.2.182", 12345)

if ping360.initialize() is False:
    print("Failed to initialize Ping!")
    exit(1)

# Server initialization
localIP = "0.0.0.0"
localPort = 42069
bufferSize = 1024

udp_server_socket = socket.socket(family=socket.AF_INET, type=socket.SOCK_DGRAM) # Create datagram socket
udp_server_socket.bind((localIP, localPort)) # Bind to address and port


# =========================
# === SERVICE FUNCTIONS ===
# =========================


def meters_per_sample(ping_message, v_sound=1500):
    """ 
    Returns the target distance per sample, in meters. 
    
    Arguments:
        ping_message: the message being analyzed.
        v_sound: the operating speed of sound in water [m/s]. Default 1500.
    """
    # Sample_period is in 25ns increments
    # Time of flight includes there and back, so divide by 2
    return v_sound * ping_message.sample_period * 12.5e-9


# ====================
# === SERVICE LOOP ===
# ====================


while True:
    # Listen for incoming datagrams from clients
    message_address_pair = udp_server_socket.recvfrom(bufferSize)
    client_message = message_address_pair[0]
    client_address = message_address_pair[1]

    # TODO: Parse client configuration requests for various parameters

    # Get data from the Ping 360
    # Transmission angle is in Gradians with 0 being forward (direction of penetrator) and increasing to 399 clockwise
    # In the current AUV configuration (penetrator facing aft)
    # 0     -> Aft
    # 100   -> Port
    # 200   -> Forward
    # 300   -> Starboard
    ping_data = ping360.transmitAngle(100)
    # distance per sample
    mps = meters_per_sample(ping_data)

    # TODO: Initialize these variables as np arrays instead of lists

    # Initializing lists
    distances = []
    intensities = []

    # Compute distances and intensities of the different samples
    for i in range(len(ping_data.msg_data)):
        distances.append(i * mps)
        intensities.append(ping_data.msg_data[i])

    # Create a CSV file of distances and intensities
    # with open('Intensities20.csv', 'w') as file:
    #     writer = csv.writer(file)
    #     for i in range(len(Distances)):
    #         writer.writerow([Distances[i], Intensity[i]])

    # Converting lists to arrays
    Array_Distances = np.array(distances)
    Array_Intensity = np.array(intensities)

    # Changes made on Wednesday
    # Below 0.75m reject all samples
    limit_low = 0.8
    limit_high = 4.0

    ## Finding the index of the 0.75m distance

    # Calculate the difference array
    difference_array_low = np.absolute(Array_Distances - limit_low)
    difference_array_high = np.absolute(Array_Distances - limit_high)

    # Find the index of minimum element from the array
    limit_low_idx = difference_array_low.argmin()
    limit_high_idx = difference_array_high.argmin()

    # Set all intensity values at a distance below 0.75m to zero
    for i in range(limit_low_idx):
        Array_Intensity[i] = 0.0

    # Find index of the true maximum return
    index_max = Array_Intensity.argmax()
    Array_Intensity_2 = Array_Intensity
    
    for i in range(len(Array_Intensity) - limit_high_idx):
        Array_Intensity_2[limit_high_idx + i] = 0.0

    # Find index of the second maximum
    Array_Intensity_2[index_max] = 0.0
    # Find second maximum
    index_max_2 = Array_Intensity_2.argmax()

    # Create a CSV file of distances and intensities cropped
    # with open('Intensities20_cropped.csv', 'w') as file:
    #     writer = csv.writer(file)
    #     for i in range(len(Array_Distances)):
    #         writer.writerow([Array_Distances[i], Array_Intensity_2[i]])

    #Difference between readings
    #difference_int = Array_Intensity[index_max] - Array_Intensity[index_max_2]
    difference_dis = Array_Distances[index_max] - Array_Distances[index_max_2]

    # Approach one: Filtering using intensity
    # if difference_int > 10:
    #     # Store intensity and distance of strongest return
    #     Intensity_max_return = Array_Intensity[index_max]
    #     Distance_max_return = Array_Distances[index_max]
    # else:
    #     # Store intensity and distance of strongest return
    #     Intensity_max_return = Array_Intensity[index_max_2]
    #     Distance_max_return = Array_Distances[index_max_2]

    # Approach two: Filtering using distance
    if difference_dis < 0:
        # Store intensity and distance of strongest return
        Intensity_max_return = Array_Intensity[index_max]
        Distance_max_return = Array_Distances[index_max]
    else:
        # Store intensity and distance of strongest return
        Intensity_max_return = Array_Intensity[index_max_2]
        Distance_max_return = Array_Distances[index_max_2]
        print('second')

    #print(Array_Intensity[index_max])
    #print(Array_Distances[index_max])
    #print(Array_Intensity[index_max_2])
    #print(Array_Disstances[index_max_2])

    print(Intensity_max_return)
    print(Distance_max_return)

    # Create a CSV file of distances and intensities cropped
    # with open('Final_readings.csv', 'a') as file:
    #     writer = csv.writer(file)
    #     writer.writerow((Intensity_max_return, Distance_max_return))


    udp_server_socket.sendto(bytearray(struct.pack("f",  Distance_max_return)), client_address)
    
