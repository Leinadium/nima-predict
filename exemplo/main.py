import socket
import json
import sys

HOST, PORT = sys.argv[1], 9999
with open('data.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
    # Connect to server and send data
    sock.connect((HOST, PORT))
    sock.sendall(json.dumps(data).encode('utf-8'))

    # Receive data from the server and shut down
    received = json.loads(sock.recv(1024).decode('utf-8'))

print("=========================")
print(f"\n\nSent:     {json.dumps(data, indent=2)}")
print("=========================")
print(f"\n\nReceived: {json.dumps(received, indent=2)}")
print("=========================")
