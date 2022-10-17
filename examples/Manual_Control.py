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

TIME = time.time()
print(TIME)
while (time.time() < TIME + 2):
    master.mav.manual_control_send(
        master.target_system,
        150, #x
        0, #y
        500, #z
        0, #r
        0) # buttons

time.sleep(3.75)
print("Timepo de Vals ")

TIME1 = time.time()
while (time.time() < TIME1 + 2):
    master.mav.manual_control_send(
        master.target_system,
        350, #x
        0, #y
        500, #z
        0, #r
        0) # buttons
    #print("Segundo velo ")



    #time.sleep(0.75)


# To active button 0 (first button), 3 (fourth button) and 7 (eighth button)
# It's possible to check and configure this buttons in the Joystick menu of QGC
#buttons = 1 + 1 << 3 + 1 << 7
#master.mav.manual_control_send(
   # master.target_system,
   # 0,
   # 0,
   # 500, # 500 means neutral throttle
   # 0,
    #buttons)