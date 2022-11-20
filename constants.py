"""
Container for all constants used in the project

CHANGELOG:
 - Version 1.0.0: Initial release
"""

__author__      = "Braidan Duffy, Humberto Lebron-Rivera, Omar Jebari, and Erbene de Castro Maia Junior"
__copyright__   = "Copyright 2022"
__credits__     = ["Braidan Duffy", "Humberto Lebron-Rivera", "Omar Jebari", "Erbene de Castro Maia Junior"]
__license__     = "MIT"
__version__     = "1.0.0"
__maintainer__  = "Braidan Duffy"
__email__       = "bduffy2018@my.fit.edu"
__status__      = "Prototype"

from pymavlink import mavutil
global master
print("Establishing connection to MAVlink server...")
# TODO: Get local client IP address and put into the mavlink connection function
master = mavutil.mavlink_connection('udpin:192.168.2.1:14550') # Opens a mavlink connection at the local server

import time
global boot_time 
boot_time = time.time()