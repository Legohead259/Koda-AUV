import sys
sys.path.insert(0, "../")

from simple_pid import PID
from constants import *
from util.commands.mav_movement import set_movement_power
from util.tasks.ping_handlers import run_ping1D_service
from pymavlink import mavutil
import numpy as np
import math

wall_controller = PID(4, 0.4, 0.05) # PID Controller for the power to maintain a distance from the wall
wall_controller.output_limits = (-1000, 1000) # Bind the limits of the controller to the operational limits of the ROV
sonar_arr = np.zeros(5) # Initialize array of values for the BN to analyze

def wall_follow(target: float=2.0, **kwargs):
    """
    Try to maintain a certain distance from the wall while moving forward using a PID controller for the translational power
    """
    PID.proportional_on_measurement = True # Debug for overshoot 

    # TODO: Continue kwarg implementation for all ping parameters
    _sonar_angle = kwargs["angle"] if "angle" in kwargs else 300
    _n_samples = kwargs["n_samples"] if "n_samples" in kwargs else 1
    _log_en = kwargs["log_en"] if "log_en" in kwargs else False
    
    # TODO: Input validation; fwd_power should be between (0, 1000]

    # Set the controller setpoint
    wall_controller.setpoint = target

    # Get current distance from SONAR
    curr_distance = run_ping1D_service(n_samples=_n_samples, log_enable=_log_en)

    # Update the required translational power using the PID control loop
    power = -int(wall_controller(curr_distance)*100)
    print(power) # DEBUG

    # TODO: Investigate deadzone implemented here

    return curr_distance, power


try:
    # Wait a heartbeat before sending commands
    print("Waiting for heartbeat")
    master.wait_heartbeat()
    
    #Move sonar head into position
    # print("Resetting sonar head position...")
    # run_ping360_service(Nsamples=10, Angle=300, Log_EN=False, Range=5, Readings=200) # Readings valid for 200-1200

    # Arm ArduSub autopilot and wait until confirmed
    print("Arming...")
    master.arducopter_arm()
    master.motors_armed_wait()

    # Set mode to DEPTH_HOLD and submerge ROV to target depth
    print("Dive dive dive!")
    # TODO: Track down NoneType bug here
    # DEPTH_HOLD_MODE = master.mode_mapping()["ALT_HOLD"]
    # while not master.wait_heartbeat().custom_mode == DEPTH_HOLD_MODE: # Set DEPTH HOLD mode
    #     master.set_mode("ALT_HOLD")
    # set_target_depth(-1.0) # Set target depth
    # set_movement_power(500, 250, 500, 0, 4) # Submerge

    # Main execution loop
    while (True):
        curr_distance, side_power = wall_follow(target=2.0)
        set_movement_power(200, side_power, 500, 0, 0.25)
        sonar_arr = np.append(sonar_arr, curr_distance)[1:] # Add the current distance to the wall to the end of the array, and drop the first index; this will keep it N samples long while updating
        print(np.round(sonar_arr, 2)) # DEBUG

except KeyboardInterrupt:
    # Safe ROV after key board interrupt (Ctrl+C) is called in the terminal
    master.arducopter_disarm()
    master.motors_disarmed_wait()

except Exception as e:
    # Safe ROV after any unhandled exception
    master.arducopter_disarm()
    master.motors_disarmed_wait()
    print(e)

