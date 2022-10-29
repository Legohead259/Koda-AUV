# Trying the movement command 


from constants import *
from util.commands.mav_movement import set_movement_power, set_target_depth
from util.tasks.ping_handlers import run_ping360_service
import socket
import struct
import pickle as pk
import numpy as np

serverAddressPort = ("192.168.2.2", 42069)
bufferSize = 2048

UDPClientSocket = socket.socket(family=socket.AF_INET, type=socket.SOCK_DGRAM)

# Configuration of sonar

range_value = 5

toserver = {
    'Number of samples' : 10,
    'Angle' : 300, #300 Starboard 100 port
    "Enable Logging" : False,
    "Range" : 5, # Range SONAR should scan [m]
    "Readings": 1200 # Number of readings Ping360 should take
}

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


try:
    # Wait a heartbeat before sending commands
    print("Waiting for heartbeat")
    master.wait_heartbeat()
    
    #Move sonar head into position
    #print("Resetting sonar head position...")
    #run_ping360_service()

    # Arm ArduSub autopilot and wait until confirmed
    print("Arming...")
    master.arducopter_arm()
    master.motors_armed_wait()

    print("Dive dive dive!")
    #set_movement_power(500, 250, 500, 0, 4) # Submerge

    Target = 2.0
    # Sending sonar configuration to server
    UDPClientSocket.sendto(pk.dumps(toserver), serverAddressPort)

    # Loading the data sent by the server
    msgFromServer = pk.loads(UDPClientSocket.recv(bufferSize))

    # Reading the dictionary sent by the server
    Distance = np.mean(msgFromServer[0])

    #Distance = run_ping360_service()
    Difference = Target - Distance

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
        Difference = Target - Distance
        print(Difference)

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