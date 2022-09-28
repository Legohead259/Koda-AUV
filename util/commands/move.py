def move_forward(heading):
    """
    Move the AUV forward along a certain heading. 
    Uses a PID controller to maintain a heading lock and feed corrections.
    
    The PID controller will map the heading deviation to either positive (clockwise) or negative (counter-clockwise) yaw rates.
    These rates are passed to the ArduSub controller via the MAVlink RC input command
    """
    pass