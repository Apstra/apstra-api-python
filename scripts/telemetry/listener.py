import socket
import aosstream_pb2
import sys

"""
This is a simple single-threaded listener. 
Use 0.0.0.0 to listen on the local host.
pick a port and pick alerts, events or perfmon
"""
l = len(sys.argv)
if l <= 3: 
    print ("Usage : listener.py host port [alerts|events|perfmon]")
    exit()
        
if l > 3  : listen_to=sys.argv[3]
if l > 2 : port = int(sys.argv[2])
if l > 1 : host = sys.argv[1]


def parse_message(data):
    pos = 0
    sm = aosstream_pb2.AosSequencedMessage()
    sm.ParseFromString(data)
    m = aosstream_pb2.AosMessage()
    m.ParseFromString(sm.aos_proto)
    print (m)

with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
    s.bind((host, port))
    print(f"Listening on {host} and {port}")
    s.listen()
    conn, addr = s.accept()
    with conn:
        print(f"Connected by {addr}")
        print("recompiled")
        while (True):
            try:
                data = conn.recv(2)
                l = int.from_bytes(data, "big")
                data = conn.recv(l)
                print ("DATA RECV")
                print (data)
                if (not data):
                    break
                parse_message(data)
            except Exception as e:
                print (e)