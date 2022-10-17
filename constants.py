"""

"""

from pymavlink import mavutil
global master
print("Establishing connection to MAVlink server...")
# TODO: Get local client IP address and put into the mavlink connection function
master = mavutil.mavlink_connection('udpin:192.168.2.6:14550') # Opens a mavlink connection at the local server

import time
global boot_time 
boot_time = time.time()