"""
Various functions for handling the heartbeat messages from MAVlink 
"""

def wait_heartbeat(master):
    '''wait for a heartbeat so we know the target system IDs'''
    print("Waiting for APM heartbeat")
    msg = master.recv_match(type='HEARTBEAT', blocking=True)
    print("Heartbeat from APM (system {0} component {1})"
        .format(master.target_system, master.target_system))
    print(msg)