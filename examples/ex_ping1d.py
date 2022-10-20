from brping import Ping1D
import time

myPing = Ping1D()
#myPing.connect_serial("COM4", 115200)
# For UDP

myPing.connect_udp("192.168.2.2", 9090)

if myPing.initialize() is False:
    print("Failed to initialize Ping!")
    exit(1)

# set the speed of sound to use for distance calculations to
# 1450000 mm/s (1450 m/s)
myPing.set_speed_of_sound(1450000)

while True:
    data = myPing.get_distance()
    if data:
        print("Distance: %s\tConfidence: %s%%" % (data["distance"], data["confidence"]))
    else:
        print("Failed to get distance data")
    time.sleep(0.1)