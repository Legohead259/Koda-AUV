import time
import math

# Import mavutil
from pymavlink import mavutil

# Create the connection
master = mavutil.mavlink_connection('udpin:192.168.2.6:14550')
boot_time = time.time()
# Wait a heartbeat before sending commands
master.wait_heartbeat()

# arm ArduSub autopilot and wait until confirmed
master.arducopter_arm()
master.motors_armed_wait()

# It is already in the Desired depth position 


# Set position target (There are different Frame https://ardupilot.org/dev/docs/copter-commands-in-guided-mode.html)

#master.mav.send(mavutil.mavlink.MAVLink_set_position_target_local_ned_message("Time to boot, Target system, Target component,
#                Reference frame, type mask, XYZ position(3), Velocities XYZ(3), Acceleration XYZ(3), Yaw, Yaw rate "))
# On the mask we can say ignore the velocity set value. 

# For Local Frame
master.mav.send(mavutil.mavlink.MAVLink_set_position_target_local_ned_message(10, master.target_system,
                master.target_component, mavutil.mavlink.MAV_FRAME_LOCAL_NED, int(0b110111000000), 10, 0, 2, 0, 0 ,0 ,0 ,0 ,0 ,0 ,0))

# Yaw target used if we want to be facing a specific direction 0 = North, 90  = East, 180 = South, 270 = West , They are in radians/sec
# Yaw Rate used if we want to be rotating constantly in a direction

# For Global Frame
# =============================================================================
# master.mav.send(mavutil.mavlink.MAVLink_set_position_target_global_int_ned_message(10, master.target_system,
#                 master.target_component, mavutil.mavlink.MAV_FRAME_GLOBAL_RELATIVE_ALT, int{0b110111111000}, int(lat * 10 ** 7), int(lon *10 **7), -0.5, 0, 0 ,0 ,0 ,0 ,0 ,0 ,0))
# Usa lat/long to travel to necesitamos coordenadas exactas
#
# =============================================================================
while 1:
    msg = master.recv_match( type='NAV_CONTROLLER_OUTPUT', blocking = True)
    print(msg) # gives the waypoint distance (until 0 meanaing we arrived)
    # Another msg can be
   # msg = master.recv_match( type = 'LOCEL_POSITION_NED', blocking = True)
   # print(msg)

# clean up (disarm) at the end
master.arducopter_disarm()
master.motors_disarmed_wait()