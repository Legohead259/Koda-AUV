"""
Master container for all commands related to moving the AUV
"""

from constants import mavutil, master, boot_time
import time


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


def move_forward(heading):
    """
    Move the AUV forward along a certain heading. 
    Uses a PID controller to maintain a heading lock and feed corrections.
    
    The PID controller will map the heading deviation to either positive (clockwise) or negative (counter-clockwise) yaw rates.
    These rates are passed to the ArduSub controller via the MAVlink RC input command
    """
    pass


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