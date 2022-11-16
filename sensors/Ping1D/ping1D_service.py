#!/usr/bin/env python

"""
ping1D_service.py: 

CHANGELOG:
 - Version 1.0.0: Initial release

TODO:
"""

__author__      = "Braidan Duffy, Humberto Lebron-Rivera, Omar Jebari, and Erbene Castros"
__copyright__   = "Copyright 2022"
__credits__     = ["Braidan Duffy", "Humberto Lebron-Rivera", "Omar Jebari", "Erbene Castros"]
__license__     = "MIT"
__version__     = "1.0.0"
__maintainer__  = "Braidan Duffy"
__email__       = "bduffy2018@my.fit.edu"
__status__      = "Development"

from os.path import exists
from brping import Ping1D
import socket
import pickle as pk
import numpy as np
import datetime

# Instantiation
ping1D = Ping1D()

ping1D.connect_serial("/dev/tty/AMA3", 115200)

if ping1D.initialize() is False:
    print("Failed to initialize Ping!")
    exit(1)

# Server intialization
localIP = "0.0.0.0"
localPort = 42070
bufferSize = 2048
log_dir_path = "/home/pi/Koda-AUV/Koda-AUV/data/" + datetime.date.today().strftime("%m%d%y") # Create string for log directory in MMDDYY format e.g. 102122
log_filename = ""

udp_server_socket = socket.socket(family=socket.AF_INET, type=socket.SOCK_DGRAM) # Create datagram socket
udp_server_socket.bind((localIP, localPort)) # Bind to address and port

for i in range(0,9999):
        log_filename = "{}/ping1D_{}.pk".format(log_dir_path, i)
        # print(log_filename) # DEBUG
        if not exists(log_filename):
            break


# =========================
# === SERVICE FUNCTIONS ===
# =========================


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
    is_logging = client_message.get("is_logging") if "log_enable" in client_message else False
    speed_of_sound = client_message.get("speed_of_sound") if "speed_of_sound" in client_message else 1450000

    # Configure Ping1D
    # TODO: Expand configuration options
    ping1D.set_range(range)
    ping1D.set_speed_of_sound(speed_of_sound)

    # Create data arrays
    distance_arr = np.zeros(n_samples)
    confidence_arr = np.zeros(n_samples)

    # Collect distance information from the sensor
    for n in range(n_samples):
        ping_data = ping1D.get_distance()
        if ping_data:
            distance_arr = np.append(distance_arr, ping_data["distance"])
            confidence_arr = np.append(distance_arr, ping_data["confidence"])
        else:
            continue
    
    # Prepare data for transmission/logging
    to_client = {
        "timestamp": datetime.now().microsecond / 1000,
        "distance": np.mean(distance_arr),
        "confidence": np.mean(confidence_arr)
    }

    if is_logging:
        with open(log_filename, 'ab') as logfile:
            pk.dump(to_client, logfile, protocol=pk.HIGHEST_PROTOCOL)

    print("[%s] Distance: %s\tConfidence: %s%%" % (
        datetime.fromtimestamp(to_client["timestamp"]),
        to_client["distance"], 
        to_client["confidence"]))
    
    # Send data to client
    udp_server_socket.sendto(pk.dumps(to_client, client_address))

