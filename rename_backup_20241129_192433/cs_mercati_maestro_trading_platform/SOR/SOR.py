import socket
import logging
import os
import signal
import sys
import threading
import time

"""
Order Router App
----------------
This application receives orders from the Trading App and forwards them to the FIX Engine.

- Receiving: TCP from Trading App on localhost:5008.
- Sending: TCP to FIX Engine on localhost:5009.
- Dependencies: None
"""

# Logging setup
log_dir = "logs"
if not os.path.exists(log_dir):
    os.makedirs(log_dir)
logging.basicConfig(filename=os.path.join(log_dir, f'orderrouter_{time.strftime("%y%m%d%H%M%S")}.log'), 
                    level=logging.DEBUG, 
                    format='%(asctime)s %(message)s')

# TCP setup
HOST = 'localhost'
PORT_RECEIVE = 5008
PORT_SEND = 5009

def signal_handler(sig, frame):
    logging.info("Order Router App interrupted and exiting gracefully.")
    sys.exit(0)

signal.signal(signal.SIGINT, signal_handler)

def handle_client(conn, addr):
    logging.debug(f'Connected by {addr}')
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.connect((HOST, PORT_SEND))
        try:
            while True:
                data = conn.recv(1024)
                if not data:
                    break
                logging.debug(f'Received order: {data.decode("utf-8")}')
                s.sendall(data)
        except Exception as e:
            logging.error(f'Exception in handling client: {e}')
        finally:
            conn.close()

def start_server():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind((HOST, PORT_RECEIVE))
        s.listen()
        logging.info('Order Router listening for connections')
        while True:
            conn, addr = s.accept()
            thread = threading.Thread(target=handle_client, args=(conn, addr), daemon=True)
            thread.start()

if __name__ == "__main__":
    start_server()
