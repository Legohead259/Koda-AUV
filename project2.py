"""
Trying the movement command 
"""

from constants import *
from util.commands.mav_movement import set_movement_power, set_target_depth
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

# Configuration of sonar
range_value = 5

toserver = {
    'Number of samples' : 10,
    'Angle' : 300, #300 Starboard 100 port
    "Enable Logging" : False,
    "Range" : 5, # Range SONAR should scan [m]
    "Readings": 1200 # Number of readings Ping360 should take
}

# Instantiate object detection parameters
sonar_arr = np.zeros(10) # Initialize array of values for the BN to analyze
# TODO: Add bayesian network stuff

# TODO: Update the run_ping360_service function
def run_ping_service():
    # Sending sonar configuration to server
    UDPClientSocket.sendto(pk.dumps(toserver), serverAddressPort)

    # Loading the data sent by the server
    msgFromServer = pk.loads(UDPClientSocket.recv(bufferSize))

    # Reading the dictionary sent by the server
    distance = msgFromServer[0]
    return np.mean(distance)

def Maintain_wall(Difference, Target = 2.0):

    # Adjust maximum power
    Max_power = 1000/4

    if Difference > 0:
        power = - int(Difference * Max_power / (Target - 0.8))
        print(power)
    else:
        power = int(Difference * Max_power / (Target - range_value))
        print(power)

    # Duration of action
    duration = 1.0

    set_movement_power(100, power, 500, 0, duration)


def wall_follow(fwd_power: int=500, target: float=2.0):
    """
    Try to maintain a certain distance from the wall while moving forward using a PID controller for the translational power
    """

    # TODO: Input validation; fwd_power should be between (0, 1000]

    # Set the controller setpoint
    wall_controller.setpoint = target

    # Get current distance from SONAR
    curr_distance = run_ping_service()

    # Update the required translational power using the PID control loop
    side_power = wall_controller(curr_distance)

    # TODO: Investigate deadzone implemented here

    # Move the ROV
    set_movement_power(fwd_power, side_power, 500, 0, 1.0)

    return curr_distance

try:
    # Wait a heartbeat before sending commands
    print("Waiting for heartbeat")
    master.wait_heartbeat()
    
    #Move sonar head into position
    print("Resetting sonar head position...")
    run_ping360_service()

    # Arm ArduSub autopilot and wait until confirmed
    print("Arming...")
    master.arducopter_arm()
    master.motors_armed_wait()

    # Set mode to DEPTH_HOLD and submerge ROV to target depth
    print("Dive dive dive!")
    DEPTH_HOLD_MODE = master.mode_mapping()["ALT_HOLD"]
    while not master.wait_heartbeat().custom_mode == DEPTH_HOLD_MODE: # Set DEPTH HOLD mode
        master.set_mode("ALT_HOLD")
    set_target_depth(-1.0) # Set target depth
    set_movement_power(500, 250, 500, 0, 4) # Submerge

    # Main execution loop
    obstacle_count = 0
    
    while (obstacle_count < 3):
        curr_distance = wall_follow(target=2.0)
        sonar_arr = np.roll(sonar_arr, -1) # Shift the current values inside the distance array one index to the left
        sonar_arr = np.append(sonar_arr, curr_distance)[1:] # Add the current distance to the wall to the end of the array, and drop the first index; this will keep it N samples long while updating
        # TODO: Implement bayesian network to determine obstacle count increment
    
    # TODO: turn right 90 degrees and move forward for 2 seconds, then re-surface

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