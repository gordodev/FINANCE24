import socket
import logging
import os
import signal
import sys
import threading
import time

"""
Market Simulator App
---------------------
This application receives orders from the FIX Engine and sends fill messages back to the FIX Engine.
The fill messages simulate trade fills and alternate between "fill 1 red" and "fill 1 blue".

- Receiving: TCP from FIX Engine on localhost:5010.
- Sending: TCP back to FIX Engine on localhost:5009.
- Dependencies: None
"""

# Logging setup
log_dir = "logs"
if not os.path.exists(log_dir):
    os.makedirs(log_dir)
logging.basicConfig(filename=os.path.join(log_dir, f'marketsimulator_{time.strftime("%y%m%d%H%M%S")}.log'), 
                    level=logging.DEBUG, 
                    format='%(asctime)s %(message)s')

# TCP setup
HOST = 'localhost'
PORT_RECEIVE = 5010
PORT_SEND = 5009

def signal_handler(sig, frame):
    logging.info("Market Simulator App interrupted and exiting gracefully.")
    sys.exit(0)

signal.signal(signal.SIGINT, signal_handler)

def handle_client(conn, addr):
    logging.debug(f'Connected by {addr}')
    try:
        color = "red"
        while True:
            data = conn.recv(1024)
            if not data:
                break
            logging.debug(f'Received order: {data.decode("utf-8")}')
            fill_message = f'fill 1 {color}'
            color = "blue" if color == "red" else "red"
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.connect((HOST, PORT_SEND))
                s.sendall(fill_message.encode('utf-8'))
                logging.debug(f'Sent fill message: {fill_message}')
    except Exception as e:
        logging.error(f'Exception in handling client: {e}')
    finally:
        conn.close()

def start_server():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind((HOST, PORT_RECEIVE))
        s.listen()
        logging.info('Market Simulator listening for connections')
        while True:
            conn, addr = s.accept()
            thread = threading.Thread(target=handle_client, args=(conn, addr), daemon=True)
            thread.start()

if __name__ == "__main__":
    start_server()
