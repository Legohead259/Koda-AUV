from brping import Ping360
import time

myPing = Ping360()
#myPing.connect_serial("COM4", 115200)
# For UDP

myPing.connect_udp("192.168.2.182", 12345)

if myPing.initialize() is False:
    print("Failed to initialize Ping!")
    exit(1)

# set the speed of sound to use for distance calculations to
# 1450000 mm/s (1450 m/s)
# myPing.set_speed_of_sound(1450000)

while True:
    for i in range(0,399):
        data = myPing.transmitAngle(i)
        if data:
            print(data)
        else:
            print("Failed to get distance data")
    time.sleep(0.5)

print(myPing.get_device_information())