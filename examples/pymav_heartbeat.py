#!/usr/bin/env python

'''
test mavlink messages
'''

from pymavlink import mavutil

def wait_heartbeat(master):
    '''wait for a heartbeat so we know the target system IDs'''
    print("Waiting for APM heartbeat")
    msg = master.recv_match(type='HEARTBEAT', blocking=True)
    print("Heartbeat from APM (system {0} component {1})"
        .format(master.target_system, master.target_system))
    print(msg)

# create a mavlink serial instance
master = mavutil.mavlink_connection('udp:localhost:14550')

wait_heartbeat(master)