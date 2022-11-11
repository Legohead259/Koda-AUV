"""
Functions for handling interactions with the Ping sensors on the AUV

CHANGELOG:
 - Version 1.0.0: Initial release
 - Version 1.1.0: Updated to include sending client configuration data to server

TODO:
 - Enable the Ping360 client script to configure Ping360 server parameters such as target angle, intensities returns, and other specifications
"""

__author__      = "Braidan Duffy, Humberto Lebron-Rivera, Omar Jebari, and Erbene de Castro Maia Junior"
__copyright__   = "Copyright 2022"
__credits__     = ["Braidan Duffy", "Humberto Lebron-Rivera", "Omar Jebari", "Erbene de Castro Maia Junior"]
__license__     = "MIT"
__version__     = "1.1.0"
__maintainer__  = "Braidan Duffy"
__email__       = "bduffy2018@my.fit.edu"
__status__      = "Prototype"

import socket
import numpy as np
import pickle as pk


def run_ping360_service(address: str="192.168.2.2", port: int=42069, buffer_size: int=1024, **config):
    """
    Opens a UDP connection to the AUV Ping360 service. This connection starts the Ping360 service's routine for collecting and reporting data. This client script will send configuration data to the server, which will then return the appropriate data from the Ping360

    Arguments:
        address: the IP address of the AUV computer running the Ping360 service (default: 192.168.2.2)
        port: the port used by the Ping360 service (default: 42069)
        buffer_size: the size of the datagram buffer, in bytes (default: 1024)
        args: various configuration parameters for the Ping360 service and client script
            e.g. speed of sound, target angle/sweeps, parse data, log data, etc.

    Returns:
        The raw, packed datagram from the Ping360 service. This will need to be unpacked and parsed
    """
    _server_address_port = (address, port) 
    _udp_client_socket = socket.socket(family=socket.AF_INET, type=socket.SOCK_DGRAM)
    
    # _udp_client_socket.sendto(b'0', _server_address_port)
    # _msg_from_server = _udp_client_socket.recvfrom(buffer_size)
    # print("Message from server: ", _msg_from_server)

    to_server = {} # Initialize configuration dictionary
    for conf, value in config.items():
        to_server[conf] = value
    # print(to_server) # DEBUG

    # Sending sonar configuration to server
    _udp_client_socket.sendto(pk.dumps(to_server), _server_address_port)

    # Loading the data sent by the server
    msgFromServer = pk.loads(_udp_client_socket.recv(buffer_size))

    # Reading the dictionary sent by the server
    distance = msgFromServer[0]
    return np.mean(distance)

    # return _msg_from_server