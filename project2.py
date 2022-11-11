"""
Trying the movement command 
"""

from auto.services.run_inferrence import get_barrel_belief
from constants import *
from util.commands.mav_movement import condition_yaw, set_movement_power, set_target_depth
from util.tasks.ping_handlers import run_ping360_service
import socket
import struct
import pickle as pk
import numpy as np
from simple_pid import PID

serverAddressPort = ("192.168.2.2", 42069)
bufferSize = 2048

UDPClientSocket = socket.socket(family=socket.AF_INET, type=socket.SOCK_DGRAM)

wall_controller = PID(1, 0.1, 0.05) # PID Controller for the power to maintain a distance from the wall
wall_controller.output_limits = (-1000, 1000) # Bind the limits of the controller to the operational limits of the ROV

# Instantiate object detection parameters
sonar_arr = np.zeros(5) # Initialize array of values for the BN to analyze
# TODO: Add bayesian network stuff

def Maintain_wall(Difference, Target = 2.0):

    # Adjust maximum power
    Max_power = 1000/4

    if Difference > 0:
        power = - int(Difference * Max_power / (Target - 0.8))
        print(power)
    else:
        power = int(Difference * Max_power / (Target - 5))
        print(power)

    # Duration of action
    duration = 1.0

    set_movement_power(100, power, 500, 0, duration)


def wall_follow(fwd_power: int=500, target: float=2.0, **args):
    """
    Try to maintain a certain distance from the wall while moving forward using a PID controller for the translational power
    """

    # TODO: Continue kwarg implementation for all ping_360 parameters
    _sonar_angle = 300 # Default angle for sonar measurements
    if "Angle" in args:
        _sonar_angle = args["Angle"]
    
    # TODO: Input validation; fwd_power should be between (0, 1000]

    # Set the controller setpoint
    wall_controller.setpoint = target

    # Get current distance from SONAR
    curr_distance = run_ping360_service(Nsamples=3, Angle=_sonar_angle, Log_EN=False, Range=5, Readings=1200)

    # Update the required translational power using the PID control loop
    side_power = wall_controller(curr_distance)

    # TODO: Investigate deadzone implemented here

    # Move the ROV
    set_movement_power(fwd_power, int(side_power*100), 500, 0, 1.0)

    return curr_distance

try:
    # Wait a heartbeat before sending commands
    print("Waiting for heartbeat")
    master.wait_heartbeat()
    
    #Move sonar head into position
    print("Resetting sonar head position...")
    run_ping360_service(Nsamples=1, Angle=300, Log_EN=False, Range=5, Readings=200) # Readings valid for 200-1200

    # Arm ArduSub autopilot and wait until confirmed
    print("Arming...")
    # master.arducopter_arm()
    # master.motors_armed_wait()

    # Set mode to DEPTH_HOLD and submerge ROV to target depth
    print("Dive dive dive!")
    # TODO: Track down NoneType bug here
    # DEPTH_HOLD_MODE = master.mode_mapping()["ALT_HOLD"]
    # while not master.wait_heartbeat().custom_mode == DEPTH_HOLD_MODE: # Set DEPTH HOLD mode
    #     master.set_mode("ALT_HOLD")
    set_target_depth(-1.0) # Set target depth
    set_movement_power(500, 250, 500, 0, 4) # Submerge

    # Main execution loop
    obstacle_count = 0
    
    while (obstacle_count < 3):
        curr_distance = wall_follow(target=2.0)
        sonar_arr = np.append(sonar_arr, curr_distance)[1:] # Add the current distance to the wall to the end of the array, and drop the first index; this will keep it N samples long while updating
        print(sonar_arr) # DEBUG
        obstacle_count += get_barrel_belief(sonar_arr)[0] > 0.6
        print(obstacle_count) # DEBUG
    
    # Stop all movement
    set_movement_power(0, 0, 500, 0)
    # Rotate 180°
    condition_yaw(180, True)
    # Return to start
    wall_follow(target=1.0, Angle=200) # Angle sets the SONAR to be looking to front of ROV

    """
    # Sending sonar configuration to server
    UDPClientSocket.sendto(pk.dumps(toserver), serverAddressPort)

    # Loading the data sent by the server
    msgFromServer = pk.loads(UDPClientSocket.recv(bufferSize))

    # Reading the dictionary sent by the server
    Distance = np.mean(msgFromServer[0])

    #Distance = run_ping360_service()
    Difference = wall_distance - Distance

    while (np.abs(Difference) > 0.1):
        # Controlling distance off-wall
        Maintain_wall(Difference)

        # Sending sonar configuration to server
        UDPClientSocket.sendto(pk.dumps(toserver), serverAddressPort)

        # Loading the data sent by the server
        msgFromServer = pk.loads(UDPClientSocket.recv(bufferSize))

        # Reading the dictionary sent by the server
        Distance = np.mean(msgFromServer[0])

        #Distance = run_ping360_service()
        Difference = wall_distance - Distance
        print(Difference)
    """

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