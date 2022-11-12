"""
Example of how to filter for specific mavlink messages coming from the
autopilot using pymavlink.

Can also filter within recv_match command - see "Read all parameters" example
"""
# Import mavutil
from pymavlink import mavutil

# Create the connection
# From topside computer
master = mavutil.mavlink_connection('udpin:192.168.2.6:14550')

while True:
    msg = master.recv_match(type='AHRS2')
    if not msg:
        continue
    print("\n\n*****Got message: %s*****" % msg.get_type())
    print(msg.get_)
        # print("Message: %s" % msg)
        # print("\nAs dictionary: %s" % msg.to_dict())
        # # Armed = MAV_STATE_STANDBY (4), Disarmed = MAV_STATE_ACTIVE (3)
        # print("\nSystem status: %s" % msg.system_status)