"""
Example of how to send MANUAL_CONTROL messages to the autopilot using
pymavlink.
This message is able to fully replace the joystick inputs.
"""
import time
import math

# Import mavutil
from pymavlink import mavutil

# Create the connection
master = mavutil.mavlink_connection('udpin:192.168.2.6:14550')
# Wait a heartbeat before sending commands
master.wait_heartbeat()

# arm ArduSub autopilot and wait until confirmed
master.arducopter_arm()
master.motors_armed_wait()

# Send a positive x value, negative y, negative z,
# positive rotation and no button.
# https://mavlink.io/en/messages/common.html#MANUAL_CONTROL
# Warning: Because of some legacy workaround, z will work between [0-1000]
# where 0 is full reverse, 500 is no output and 1000 is full throttle.
# x,y and r will be between [-1000 and 1000].


def set_target_fordward(X,Y,Z,R):
    # Creates a time variable from EPOCH
    TIME = time.time()

    # While 4 seconds have not passed go fordward
    while (time.time() < TIME + 2):
        master.mav.manual_control_send(
            master.target_system,
            X, #350,  # x
            Y, #0,    # y
            Z, #500,  # z
            R, #0,    # r
            0)        # buttons
        # print("Tiempo de Vals")
        time.sleep(0.75)

#time.sleep(3.75)
set_target_fordward(0,0,390,0)

set_target_fordward(50,0,500,0)

set_target_fordward(350,0,500,0)

set_target_fordward(350,0,500,0)

set_target_fordward(350,0,500,0)

set_target_fordward(350,0,500,0)

set_target_fordward(350,0,500,0)

set_target_fordward(350,0,500,0)

set_target_fordward(350,0,500,0)

set_target_fordward(50,0,500,0)

set_target_fordward(0,0,600,0)

master.arducopter_disarm()
master.motors_disarmed_wait()
