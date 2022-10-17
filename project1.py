"""
Project 1 program for running the ROV inside a pool.

CONOPS: The ROV will start from one edge of the pool and be placed about two meters away from the wall on its starboard side. The AUV will dive to about one meter and proceed along the width of the pool stopping every meter or so to determine the distance from the wall using the Ping 360 SONAR. This will occur multiple times until the AUV reaches the other side of the pool, where it will ascend and safe itself. Somewhere along the wall, a barrel or similar obstruction will be placed that will cause a noticeable "blip" in the SONAR distance measurements. These measurements will be fed into a Bayesian network to determine the probability of the robot having passed by a barrel or not.

CHANGELOG:
 - Version 1.0.0: Initial release
 - Version 1.1.0: Refactored to clean up code and test new project directory layout
"""

__author__      = "Braidan Duffy, Humberto Lebron-Rivera, Omar Jebari, and Erbene Castros"
__copyright__   = "Copyright 2022"
__credits__     = ["Braidan Duffy", "Humberto Lebron-Rivera", "Omar Jebari", "Erbene Castros"]
__license__     = "MIT"
__version__     = "1.1.0"
__maintainer__  = "Braidan Duffy"
__email__       = "bduffy2018@my.fit.edu"
__status__      = "Prototype"

from constants import *
from util.commands.mav_movement import send_movement_power, set_target_depth
from util.tasks.ping_handlers import run_ping360_service

try:
    # Wait a heartbeat before sending commands
    print("Waiting for heartbeat")
    master.wait_heartbeat()
    
    # Move sonar head into position
    print("Resetting sonar head position...")
    run_ping360_service()

    # Arm ArduSub autopilot and wait until confirmed
    print("Arming...")
    # master.arducopter_arm()
    # master.motors_armed_wait()

    # Set DEPTH_HOLD mode
    print("Setting DEPTH_HOLD mode")
    while not master.wait_heartbeat().custom_mode == 2:
        master.set_mode('ALT_HOLD')

    # Set desired depth
    print("Setting target depth...")
    set_target_depth(-125.0)

    print("Dive dive dive!")
    send_movement_power(0, 0, 250, 0, 1.75) # Submerge

    for i in range (0, 7): # Take a certain number of steps (samples)
        send_movement_power(350, 0, 500, 0, 4) # Move forward at 1/3 speed
        send_movement_power(0, 0, 500, 0, 1) # Stop all movement
        run_ping360_service() # Have the Ping360 collect readings
        # time.sleep(0.5) # Simulate taking readings

    set_target_depth(-0.0) # Set target depth to the surface
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