# KODA AUV TROUBLESHOOTING GUIDE

## MAVLink Communications Not Working

### ROV Connected, but MAVlink messages not being received
Ensure that the end point pointer in the "Endpoints" manager in BlueOS is pointing to the IP address of the topside computer

## Ping SONARs

### Ping 1D Not Showing Up Even Though it is Plugged into Serial Port
Verify connection to Serial port and number
1. Open QGroundControl and go to the "Parameters" tab
2. Modify the `SERIALn_MODE` to `None` where 'n' is the Serial port number on the Navigator board
3. Restart the autopilot firmware using the "General" tab in BlueOS
4. Restart the BlueOS Docker container