from brping import Ping360
import time
import socket
import struct

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
    data = ping360.transmitAngle(100)
    print(data.data) # DEBUG
    max_intensity_idx = data.msg_data.index(max(data.msg_data))
    sample_distance = max_intensity_idx * meters_per_sample(data)
    print(sample_distance)  # DEBUG
    Humbi = []
    for i in range(len(data.msg_data)):
        Humbi.append(data.msg_data[i] * meters_per_sample(data))
    print('%.03f' % Humbi) #HO -- TESTING
    udp_server_socket.sendto(bytearray(struct.pack("f", max(Humbi))), client_address)
    #udp_server_socket.sendto(bytearray(struct.pack("f", sample_distance)), client_address)
    
