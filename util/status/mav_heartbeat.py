"""
Various functions for handling the heartbeat messages from MAVlink 

CHANGELOG:
 - Version 1.0.0: Initial Release
"""

__author__      = "Braidan Duffy, Humberto Lebron-Rivera, Omar Jebari, and Erbene de Castro Maia Junior"
__copyright__   = "Copyright 2022"
__credits__     = ["Braidan Duffy", "Humberto Lebron-Rivera", "Omar Jebari", "Erbene de Castro Maia Junior"]
__license__     = "MIT"
__version__     = "1.0.0"
__maintainer__  = "Braidan Duffy"
__email__       = "bduffy2018@my.fit.edu"
__status__      = "Prototype"


def wait_heartbeat(master):
    """
    Wait for a heartbeat so we know the target system IDs

    Arguments:
        master: the MAVlink master object for the heartbeat detection 
    """

    print("Waiting for APM heartbeat")
    msg = master.recv_match(type='HEARTBEAT', blocking=True)
    print("Heartbeat from APM (system {0} component {1})"
        .format(master.target_system, master.target_system))
    print(msg)