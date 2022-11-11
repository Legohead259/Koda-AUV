"""
Container for all commands related to moving the AUV

CHANGELOG:
 - Version 1.0.0: Initial release
 - Version 1.0.1: Modified documentation
"""

__author__      = "Braidan Duffy, Humberto Lebron-Rivera, Omar Jebari, and Erbene de Castro Maia Junior"
__copyright__   = "Copyright 2022"
__credits__     = ["Braidan Duffy", "Humberto Lebron-Rivera", "Omar Jebari", "Erbene de Castro Maia Junior"]
__license__     = "MIT"
__version__     = "1.0.1"
__maintainer__  = "Braidan Duffy"
__email__       = "bduffy2018@my.fit.edu"
__status__      = "Prototype"

from constants import mavutil, master, boot_time
import time
from pymavlink.quaternion import QuaternionBase
import math


def set_movement_power(x: int, y: int, z: int, r: int, t: float=2):
    '''
    Send a joystick-input movement command to the AUV using MAVlink.
    The robot control firmware interprets these values as PWM outputs to the thruster ESCs, thus controlling direction and speed.

    Arguments:
        x: the longitudinal power of the thrusters from [-1000, 1000], where positive is forward
        y: the lateral power of the thrusters from [-1000, 1000], where positive is right (?)
        z: the normal power of the thrusters from [0, 1000], where [0, 500) is down, 500 is neutral, and (500, 1000] is up
        r: the rotation power from [-1000, 1000], where positive is clockwise rotation
        t: the amount of time the movement command should be executed in seconds. Defaults to 2. 
        Note: if this value is -1, the command will only be sent once; useful for functions that need to precisely control the function 
    '''

    if t == -1: # Check if command is only to be sent once
        master.mav.manual_control_send(
            master.target_system,
            x, # x
            y, # y
            z, # z
            r, # r
            0) # buttons
        return
    
    # Creates a time variable from EPOCH
    cmd_start_time = time.time()

    # While t seconds have not passed, move as specified
    while (time.time() < cmd_start_time + t):
        master.mav.manual_control_send(
            master.target_system,
            x, # x
            y, # y
            z, # z
            r, # r
            0) # buttons


def set_target_attitude(roll:float , pitch: float, yaw: float):
    """
    Sets the target attitude for the AUV using the internal controller and control algorithms. The body orientation axes are determined in the aeronautical format (x -> forward, y -> right, z -> down).

    Arguments:
        roll: the rotation of the AUV around the x-axis in degrees [-180, 180]
        pitch: the rotation of the AUV around the y-axis in degrees [-180, 180]
        yaw: the rotation of the AUV around the z-axis in degrees [0, 359]

    TODO: Return the current AUV attitude (?)
    """
    master.mav.set_attitude_target_send(
        int(1e3 * (time.time() - boot_time)), # ms since boot
        master.target_system, master.target_component,
        # allow throttle to be controlled by depth_hold mode
        mavutil.mavlink.ATTITUDE_TARGET_TYPEMASK_THROTTLE_IGNORE,
        # -> attitude quaternion (w, x, y, z | zero-rotation is 1, 0, 0, 0)
        QuaternionBase([math.radians(angle) for angle in (roll, pitch, yaw)]),
        0, 0, 0, 0 # roll rate, pitch rate, yaw rate, thrust
    )


def set_target_depth(depth: float):
    """
    Sets the target depth while in depth-hold mode. When the ROV is armed and in depth-hold mode, it will attempt to maintain the specified altitude.

    Uses https://mavlink.io/en/messages/common.html#SET_POSITION_TARGET_GLOBAL_INT

    'depth' is technically an altitude, so set as negative meters below the surface
        -> set_target_depth(-1.5) # sets target to 1.5m below the water surface.

    Arguments:
        depth: the desired depth of the ROV in meters
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


def condition_yaw(heading, relative=False):
    """
    Send MAV_CMD_CONDITION_YAW message to point vehicle at a specified heading (in degrees).

    This method sets an absolute heading by default, but you can set the `relative` parameter
    to `True` to set yaw relative to the current yaw heading.

    By default the yaw of the vehicle will follow the direction of travel. After setting 
    the yaw using this function there is no way to return to the default yaw "follow direction 
    of travel" behaviour (https://github.com/diydrones/ardupilot/issues/2427)

    For more information see: 
    http://copter.ardupilot.com/wiki/common-mavlink-mission-command-messages-mav_cmd/#mav_cmd_condition_yaw
    """
    if relative:
        is_relative = 1 #yaw relative to direction of travel
    else:
        is_relative = 0 #yaw is an absolute angle
    # create the CONDITION_YAW command using command_long_encode()
    master.mav.command_long_send(
        0, 0,    # target system, target component
        mavutil.mavlink.MAV_CMD_CONDITION_YAW, #command
        0, #confirmation
        heading,    # param 1, yaw in degrees
        0,          # param 2, yaw speed deg/s
        1,          # param 3, direction -1 ccw, 1 cw
        is_relative, # param 4, relative offset 1, absolute angle 0
        0, 0, 0)    # param 5 ~ 7 not used