#!/usr/bin/env python

"""
ping360_service.py: This script starts a local server that connects to the Ping360 on the AUV and handles gathering data from it.
This script is intended to run locally on the Raspberry Pi onboard the AUV and access the Ping 360 over a UDP connection.

Client scripts can open a UDP connection to this service's port and the server will command the Ping 360 to begin gathering data along a heading. This service will then filter and parse the data such that the strongest return signal and distance from the AUV is returned to the client. The client may re-connect to the server as many times as desired and receive data.

Note: On start-up there may be a slight delay between client connection and server data sent as the Ping360 SONAR head has to rotated around to the specified bearing. This delay will also be present if different services are trying to work with the Ping 360 such as Ping Viewer. Therefore, it is **not** advised that this service runs consecutively with the Blue Robotics Ping Viewer application.

CHANGELOG:
 - Version 1.0.0: Initial release
 - Version 1.1.0: Added ability for client to configure sensor data

TODO:
 - Figure out how to properly filter max intensity accounting for reverb in signal
 - Add CLI argument parser for Ping 360 Serial (with port) or UDP (with IP address and port)
"""

__author__      = "Braidan Duffy, Humberto Lebron-Rivera, Omar Jebari, and Erbene Castros"
__copyright__   = "Copyright 2022"
__credits__     = ["Braidan Duffy", "Humberto Lebron-Rivera", "Omar Jebari", "Erbene Castros"]
__license__     = "MIT"
__version__     = "1.1.0"
__maintainer__  = "Braidan Duffy"
__email__       = "bduffy2018@my.fit.edu"
__status__      = "Development"

from brping import Ping360
import numpy as np
import socket
import pickle as pk
from datetime import date
from os.path import exists

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
bufferSize = 2048
log_dir_path = "/home/pi/Koda-AUV/Koda-AUV/data/" + date.today().strftime("%m%d%y") # Create string for log directory in MMDDYY format e.g. 102122
log_filename = ""

udp_server_socket = socket.socket(family=socket.AF_INET, type=socket.SOCK_DGRAM) # Create datagram socket
udp_server_socket.bind((localIP, localPort)) # Bind to address and port

# =========================
# === SERVICE FUNCTIONS ===
# =========================


def set_ping360_range(range=2, v_sound=1480):
    """
    """
    _sample_period = int(range/(v_sound * ping360.get_device_data()["number_of_samples"] * 12.5e-9))
    return ping360.set_sample_period(_sample_period)


def meters_per_sample(ping_message, v_sound=1480):
    """
    Returns the target distance per sample, in meters. 
    
    Arguments:
        'ping_message' is the message being analysed.
        'v_sound' is the operating speed of sound [m/s]. Default 1500.
    """
    # sample_period is in 25ns increments
    # time of flight includes there and back, so divide by 2
    return v_sound * ping_message.sample_period * 12.5e-9


# ====================
# === SERVICE LOOP ===
# ====================


while True:
    # Listen for incoming datagrams from clients
    message_address_pair = udp_server_socket.recvfrom(bufferSize)
    client_message = pk.loads(message_address_pair[0])
    client_address = message_address_pair[1]

    # Reading the dictionary sent by the client
    N_samples = client_message.get("Nsamples")
    Angle = client_message.get("Angle")
    logging = client_message.get("Log_EN")
    ping360_range = client_message.get("Range")
    readings = client_message.get("Readings")

    # Configure Ping360
    ping360.set_number_of_samples(int(readings))
    set_ping360_range(ping360_range)

    # Get data from the Ping 360
    # Transmission angle is in Gradians with 0 being forward (direction of penetrator) and increasing to 399 clockwise
    # In the current AUV configuration (penetrator facing aft)
    # 0     -> Aft
    # 100   -> Port
    # 200   -> Forward
    # 300   -> Starboard
    ping_data = ping360.transmitAngle(Angle)
    # distance per sample
    mps = meters_per_sample(ping_data)

    # Initializing numpy arrays
    Array_Distances = np.zeros((N_samples, len(ping_data.msg_data)))
    Array_Intensity = np.zeros((N_samples, len(ping_data.msg_data)))
    index_max = np.zeros(N_samples)
    Intensity_max_return = np.zeros(N_samples)
    Distance_max_return = np.zeros(N_samples)

    for n in range(N_samples):
        # ping_data = None
        # while ping_data is None:
        ping_data = ping360.transmitAngle(Angle)

        # Compute distances and intensities of the different samples
        for i in range(len(ping_data.msg_data)):
            Array_Distances[n, i] = i * mps
            Array_Intensity[n, i] = ping_data.msg_data[i]

        # Reject all samples below 0.8 meters
        limit_low = 0.8
        limit_high = 5.0

        # # # Calculate the difference array
        # difference_array_low = np.absolute(Array_Distances[n, :] - limit_low)
        # difference_array_high = np.absolute(Array_Distances[n, :] - limit_high)

        # # Find the index of minimum element from the array
        # limit_low_idx = difference_array_low.argmin()
        # limit_high_idx = difference_array_high.argmin()

        low_cutoff_index = int(limit_low/mps)
        high_cutoff_index = int(limit_high/mps)

        # Set all intensity values at a distance below 0.75m to zero
        Array_int = Array_Intensity[n, :]
        for i in range(low_cutoff_index):
            Array_int[i] = 0.0

        # Set all intensity values at a distance beyond 5m to zero
        for i in range(len(Array_int) - high_cutoff_index):
            Array_int[high_cutoff_index + i] = 0.0

        # Find index of the true maximum return
        index_max[n] = Array_int.argmax()

        # Finding max intensity and distance where it was measured
        Intensity_max_return[n] = Array_Intensity[n, int(index_max[n])]
        Distance_max_return[n] = Array_Distances[n, int(index_max[n])]

    # Create a dictionary of objects to send to client
    to_client = {
        'dimensions': Array_Distances,
        'intensities' : Array_Intensity,
        'likely_max_index' : index_max,
        'likely_distance' : Distance_max_return,
        'intensity_likely_distance' : Intensity_max_return
    }

    for i in range(0,9999):
        log_filename = "{}/Ping360_data_{}.pk".format(log_dir_path, i)
        # print(log_filename) # DEBUG
        if not exists(log_filename):
            break

    with open(log_filename, 'ab') as workspace:
        pk.dump(to_client, workspace, protocol=pk.HIGHEST_PROTOCOL)
    
    print(to_client["likely_distance"])
    print(to_client["dimensions"])
    udp_server_socket.sendto(pk.dumps((to_client["likely_distance"], to_client["intensity_likely_distance"])), client_address)


