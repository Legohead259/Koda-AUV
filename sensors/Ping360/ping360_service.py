#!/usr/bin/env python

"""
ping360_service.py: This script starts a local server that connects to the Ping360 on the AUV and handles gathering data from it.
This script is intended to run locally on the Raspberry Pi onboard the AUV and access the Ping 360 over a UDP connection.

Client scripts can open a UDP connection to this service's port and the server will command the Ping 360 to begin gathering data along a heading. This service will then filter and parse the data such that the strongest return signal and distance from the AUV is returned to the client. The client may re-connect to the server as many times as desired and receive data.

Note: On start-up there may be a slight delay between client connection and server data sent as the Ping360 SONAR head has to rotated around to the specified bearing. This delay will also be present if different services are trying to work with the Ping 360 such as Ping Viewer. Therefore, it is **not** advised that this service runs consecutively with the Blue Robotics Ping Viewer application.

CHANGELOG:
 - Version 1.0.0: Initial release
 - Version 1.1.0: Added ability for client to configure sensor data
 - Version 1.1.1: Minor tweaks to API format; Fixed 'NoneType' error for Ping360 data

TODO:
 - Figure out how to properly filter max intensity accounting for reverb in signal
 - Add CLI argument parser for Ping 360 Serial (with port) or UDP (with IP address and port)
 - Specify timeout for receiving Ping360 data
"""

__author__      = "Braidan Duffy, Humberto Lebron-Rivera, Omar Jebari, and Erbene Castros"
__copyright__   = "Copyright 2022"
__credits__     = ["Braidan Duffy", "Humberto Lebron-Rivera", "Omar Jebari", "Erbene Castros"]
__license__     = "MIT"
__version__     = "1.1.1"
__maintainer__  = "Braidan Duffy"
__email__       = "bduffy2018@my.fit.edu"
__status__      = "Development"

import datetime
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
last_log_number = 0

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
    n_samples = client_message.get("n_samples") if "n_samples" in client_message else 1
    angle = client_message.get("angle") if "angle" in client_message else 300
    is_logging = client_message.get("log_en") if "log_en" in client_message else False
    range = client_message.get("range") if "range" in client_message else 5
    readings = client_message.get("readings") if "readings" in client_message else 1200

    # Configure Ping360
    ping360.set_number_of_samples(int(readings))
    set_ping360_range(range)

    # Get data from the Ping 360
    # Transmission angle is in Gradians with 0 being forward (direction of penetrator) and increasing to 399 clockwise
    # In the current AUV configuration (penetrator facing aft)
    # 0     -> Aft
    # 100   -> Port
    # 200   -> Forward
    # 300   -> Starboard
    ping_data = ping360.transmitAngle(angle)
    mps = meters_per_sample(ping_data) # Distance per sample

    # Initializing numpy arrays
    distance_mat = np.zeros((n_samples, len(ping_data.msg_data)))
    intensity_mat = np.zeros((n_samples, len(ping_data.msg_data)))
    index_max_arr = np.zeros(n_samples)
    max_intensity_arr = np.zeros(n_samples)
    max_distance_arr = np.zeros(n_samples)

    for n in range(n_samples):
        ping_data = ping360.transmitAngle(angle)
        if not ping_data: # Check for valid response; if none received, ignore and continue with loop
            continue
            
        # Compute distances and intensities of the different samples
        for i in range(len(ping_data.msg_data)):
            distance_mat[n, i] = i * mps
            intensity_mat[n, i] = ping_data.msg_data[i]

        # Reject all samples below 0.8 meters
        LIMIT_LOW = 0.8
        LIMIT_HIGH = range

        LOW_CUTOFF_INDEX = int(LIMIT_LOW/mps)
        HIGH_CUTOFF_INDEX = int(LIMIT_HIGH/mps)

        # Set all intensity values at a distance below LIMIT_LOW to 0
        intensity_arr = intensity_mat[n, :]
        for i in range(LOW_CUTOFF_INDEX):
            intensity_arr[i] = 0.0

        # Set all intensity values at a distance beyond LIMIT_HIGH to 0
        for i in range(len(intensity_arr) - HIGH_CUTOFF_INDEX):
            intensity_arr[HIGH_CUTOFF_INDEX + i] = 0.0

        # Find index of the true maximum return
        index_max_arr[n] = intensity_arr.argmax()

        # Finding max intensity and distance where it was measured
        max_intensity_arr[n] = intensity_mat[n, int(index_max_arr[n])]
        max_distance_arr[n] = distance_mat[n, int(index_max_arr[n])]

    # Preparing a dictionary for logging/transmission
    to_client = {
        "timestamp": datetime.now().microsecond / 1000,
        'distance_matrix': distance_mat,
        'intensities_matrix' : intensity_mat,
        'max_index' : index_max_arr,
        'distance' : max_distance_arr,
        'intensity' : max_intensity_arr
    }

    if is_logging:
        log_filename = "{}/Ping360_data_{}.pk".format(log_dir_path, last_log_number)
        # print(log_filename) # DEBUG
        with open(log_filename, 'wb') as workspace:
            pk.dump(to_client, workspace, protocol=pk.HIGHEST_PROTOCOL)
        last_log_number = last_log_number + 1
    
    print(to_client["distance"]) # Debug
    print(to_client["dimensions"]) # Debug
    udp_server_socket.sendto(pk.dumps((to_client["distance"], to_client["intensity"])), client_address)


