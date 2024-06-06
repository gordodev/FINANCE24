import socket
import struct
import time
import logging
import os
import signal
import random

# Configuration
MULTICAST_GROUP = '224.1.1.1'
MULTICAST_PORT = 5007
LOG_DIR = 'logs'
LOG_FILE = f"{LOG_DIR}/marketdata{time.strftime('%y%m%d%H%M%S')}.log"

# Ensure log directory exists
os.makedirs(LOG_DIR, exist_ok=True)

# Logging configuration
logging.basicConfig(filename=LOG_FILE, level=logging.DEBUG, format='%(asctime)s %(message)s')
logging.debug('Market Data App started.')

def send_market_data():
    """Function to send random 'blue' or 'red' messages via multicast every 1-3 seconds."""
    multicast_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
    ttl = struct.pack('b', 1)
    multicast_socket.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, ttl)
    
    while True:
        message = random.choice(['blue', 'red'])
        multicast_socket.sendto(message.encode('utf-8'), (MULTICAST_GROUP, MULTICAST_PORT))
        logging.debug(f'Sent message: {message}')
        time.sleep(random.randint(1, 3))

def handle_exit(signum, frame):
    """Handle exit signals for graceful shutdown."""
    logging.debug('Market Data App shutting down.')
    exit(0)

# Signal handling for graceful shutdown
signal.signal(signal.SIGINT, handle_exit)
signal.signal(signal.SIGTERM, handle_exit)

if __name__ == "__main__":
    send_market_data()
