"""

"""

from pymavlink import mavutil
global master
print("Establishing connection to MAVlink server...")
master = mavutil.mavlink_connection('udpin:0.0.0.0:14550') # Opens a mavlink connection at the local server

import time
global boot_time 
boot_time = time.time()