"""
Example of how to send MANUAL_CONTROL messages to the autopilot using
pymavlink.
This message is able to fully replace the joystick inputs.
"""
import time
import math
import socket
from pymavlink import mavutil

serverAddressPort = ("192.168.2.2", 42069)
bufferSize = 1024

UDPClientSocket = socket.socket(family=socket.AF_INET, type=socket.SOCK_DGRAM)

boot_time = time.time()

def run_ping_service():
    UDPClientSocket.sendto(b'0', serverAddressPort)
    msgFromServer = UDPClientSocket.recvfrom(bufferSize)
    print("Message from server: ", msgFromServer)
    # UDPClientSocket.sendto(b'0', serverAddressPort)
    # while not UDPClientSocket.recvfrom(bufferSize):
    #     send_movement_power(0, 0, 500, 0, 1)


def set_target_depth(depth):
    """ Sets the target depth while in depth-hold mode.

    Uses https://mavlink.io/en/messages/common.html#SET_POSITION_TARGET_GLOBAL_INT

    'depth' is technically an altitude, so set as negative meters below the surface
        -> set_target_depth(-1.5) # sets target to 1.5m below the water surface.

    """
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


def send_movement_power(X: int, Y: int, Z: int, R: int, t: float):
    '''
    Send a positive x value, negative y, negative z,
    positive rotation and no button.
    https://mavlink.io/en/messages/common.html#MANUAL_CONTROL
    Warning: Because of some legacy workaround, z will work between [0-1000]
    where 0 is full reverse, 500 is no output and 1000 is full throttle.
    x,y and r will be between [-1000 and 1000].
    '''

    # Creates a time variable from EPOCH
    cmd_start_time = time.time()

    # While t seconds have not passed, move as specified
    while (time.time() < cmd_start_time + t):
        master.mav.manual_control_send(
            master.target_system,
            X, # x
            Y, # y
            Z, # z
            R, # r
            0) # buttons
        time.sleep(0.75)

try:
    # Create the connection
    print("Establishing connection...")
    master = mavutil.mavlink_connection('udpin:192.168.2.6:14550')

    # Wait a heartbeat before sending commands
    print("Waiting for heartbeat")
    master.wait_heartbeat()
    
    # Move sonar head into position
    print("Resetting sonar head position...")
    # run_ping_service()

    # Arm ArduSub autopilot and wait until confirmed
    print("Arming...")
    master.arducopter_arm()
    master.motors_armed_wait()

    # Set desired depth
    print("Setting target depth...")
    set_target_depth(-125.0)

    print("Dive dive dive!")
    send_movement_power(0, 0, 250, 0, 1.75) # Submerge
    time.sleep(2)
    send_movement_power(50, 0, 500, 0, 2)

    for i in range (0, 7): # Take a certain number of steps (samples)
        send_movement_power(350, 0, 500, 0, 4) # Move forward at 1/3 speed
        send_movement_power(0, 0, 500, 0, 1) # Stop all movement
        # run_ping_service() # Have the Ping360 collect readings
        time.sleep(2) # Simulate taking readings
        # TODO: Call UDP client script, get data

    send_movement_power(0, 0, 750, 0, 4) # Ascend

    # Safe ROV after operation completes
    master.arducopter_disarm()
    master.motors_disarmed_wait()

except KeyboardInterrupt:
    # Safe ROV after key board interrupt (Ctrl+C) is called in the terminal
    master.arducopter_disarm()
    master.motors_disarmed_wait()

except Exception as e:
    # Safe ROV after any unhandled exception
    master.arducopter_disarm()
    master.motors_disarmed_wait()
    print(e)