"""
Functions for handling interactions with the Ping sensors on the AUV
"""
import socket


def run_ping360_service(address: str="192.168.2.2", port: int=42069, buffer_size: int=1024):
    _server_address_port = (address, port) 
    _udp_client_socket = socket.socket(family=socket.AF_INET, type=socket.SOCK_DGRAM)
    
    _udp_client_socket.sendto(b'0', _server_address_port)
    _msg_from_server = _udp_client_socket.recvfrom(buffer_size)
    print("Message from server: ", _msg_from_server)