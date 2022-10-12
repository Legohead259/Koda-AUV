# Starting the Frankenstein

# Import some Python Libraries 
from ctypes import sizeof
from brping import Ping360
import numpy as np
import time
import socket
import struct
import csv
import math

# Import mavutil
from pymavlink import mavutil

# Imports for attitude
from pymavlink.quaternion import QuaternionBase


# =========================================================================================================================================================
# =================================================================== UDP_Server Initialization ===========================================================
# ========================================================================================================================================================= 

# Ping initialization
ping360 = Ping360()

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
    with open('Intensities7.csv', 'w') as file:
        writer = csv.writer(file)
        for i in range(len(Distances)):
            writer.writerow([Distances[i], Intensity[i]])

# Converting lists to arrays
    Array_Distances = np.array(Distances)
    Array_Intensity = np.array(Intensity)

# Below 0.75m reject all samples
    Limit = 0.75

#### Finding the index of the 0.75m distance

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
    
    
# =========================================================================================================================================================
# =================================================================== Koda Initialization =================================================================
# ========================================================================================================================================================= 
  
# Create the connection
master = mavutil.mavlink_connection('udpin:192.168.2.6:14550')
boot_time = time.time()

# Wait a heartbeat before sending commands
master.wait_heartbeat()

# arm ArduSub autopilot and wait until confirmed
master.arducopter_arm()
master.motors_armed_wait()    
           
# =========================================================================================================================================================
# =================================================================== Depth Hold ==========================================================================
# ========================================================================================================================================================= 
    
def set_target_depth(depth):

    master.mav.set_position_target_global_int_send(
        int(1e3 * (time.time() - boot_time)), # ms since boot
        master.target_system, master.target_component,
        coordinate_frame=mavutil.mavlink.MAV_FRAME_GLOBAL_INT,
        type_mask=( # ignore everything except z position
            mavutil.mavlink.POSITION_TARGET_TYPEMASK_X_IGNORE |
            mavutil.mavlink.POSITION_TARGET_TYPEMASK_Y_IGNORE |
            # DON'T mavutil.mavlink.POSITION_TARGET_TYPEMASK_Z_IGNORE |
            mavutil.mavlink.POSITION_TARGET_TYPEMASK_VX_IGNORE |
            mavutil.mavlink.POSITION_TARGET_TYPEMASK_VY_IGNORE |
            mavutil.mavlink.POSITION_TARGET_TYPEMASK_VZ_IGNORE |
            mavutil.mavlink.POSITION_TARGET_TYPEMASK_AX_IGNORE |
            mavutil.mavlink.POSITION_TARGET_TYPEMASK_AY_IGNORE |
            mavutil.mavlink.POSITION_TARGET_TYPEMASK_AZ_IGNORE |
            # DON'T mavutil.mavlink.POSITION_TARGET_TYPEMASK_FORCE_SET |
            mavutil.mavlink.POSITION_TARGET_TYPEMASK_YAW_IGNORE |
            mavutil.mavlink.POSITION_TARGET_TYPEMASK_YAW_RATE_IGNORE
        ), lat_int=0, lon_int=0, alt=depth, # (x, y WGS84 frame pos - not used), z [m]
        vx=0, vy=0, vz=0, # velocities in NED frame [m/s] (not used)
        afx=0, afy=0, afz=0, yaw=0, yaw_rate=0
        # accelerations in NED frame [N], yaw, yaw_rate
        #  (all not supported yet, ignored in GCS Mavlink)
    )

def set_target_attitude(roll, pitch, yaw): # Angles are in Degrees

    master.mav.set_attitude_target_send(
        int(1e3 * (time.time() - boot_time)), # ms since boot
        master.target_system, master.target_component,
        # allow throttle to be controlled by depth_hold mode
        mavutil.mavlink.ATTITUDE_TARGET_TYPEMASK_THROTTLE_IGNORE,
        # -> attitude quaternion (w, x, y, z | zero-rotation is 1, 0, 0, 0)
        QuaternionBase([math.radians(angle) for angle in (roll, pitch, yaw)]),
        0, 0, 0, 0 # roll rate, pitch rate, yaw rate, thrust) # The parentesis was in the next line (just in case)
        
# set the desired operating mode
DEPTH_HOLD = 'ALT_HOLD'
DEPTH_HOLD_MODE = master.mode_mapping()[DEPTH_HOLD]
while not master.wait_heartbeat().custom_mode == DEPTH_HOLD_MODE:
    master.set_mode(DEPTH_HOLD)

# set a depth target
set_target_depth(-100.0)

time.sleep(0)

# Can probably take this out and just have it after it comes to the surface 
# clean up (disarm) at the end
master.arducopter_disarm()
master.motors_disarmed_wait()

# =========================================================================================================================================================
# =================================================================== Fordward ============================================================================
# ========================================================================================================================================================= 

# Creates a time variable from EPOCH
TIME = time.time()

# While 4 seconds have not passed go fordward
while (time.time() < TIME + 4):
    master.mav.manual_control_send(
        master.target_system,
        350,  # x
        0,    # y
        500,  # z
        0,    # r
        0)    # buttons

    #time.sleep(0.75)

# There was something for the buttons so i Deleted it 


# =========================================================================================================================================================
# =================================================================== Surface =============================================================================
# ========================================================================================================================================================= 

# Come back to the surface 
set_target_depth(0.0)
        
# Disarm the vehicle at the end of the run 
master.arducopter_disarm()
master.motors_disarmed_wait()

