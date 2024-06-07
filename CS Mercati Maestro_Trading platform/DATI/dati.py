import socket
import struct
import time
import random
import logging
import os
import signal
import sys

"""
Market Data App
---------------
This application simulates a market data feed, sending random "blue" or "red" messages via multicast
every 1-3 seconds. It acts as the data source for the trading platform.

- Sending: Multicast to 224.1.1.1 on port 5007.
- Dependencies: None
"""

# Logging setup
log_dir = "logs"
if not os.path.exists(log_dir):
    os.makedirs(log_dir)
logging.basicConfig(filename=os.path.join(log_dir, f'marketdata_{time.strftime("%y%m%d%H%M%S")}.log'), 
                    level=logging.DEBUG, 
                    format='%(asctime)s %(message)s')

# Multicast setup
MCAST_GRP = '224.1.1.1'
MCAST_PORT = 5007

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
sock.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, 2)

def signal_handler(sig, frame):
    logging.info("Market Data App interrupted and exiting gracefully.")
    sys.exit(0)

signal.signal(signal.SIGINT, signal_handler)

try:
    while True:
        # Generate a random market data message
        message = random.choice(['blue', 'red'])
        logging.debug(f'Sending market data message: {message}')
        sock.sendto(message.encode('utf-8'), (MCAST_GRP, MCAST_PORT))
        time.sleep(random.randint(1, 3))
except Exception as e:
    logging.error(f'Exception occurred: {e}')
finally:
    logging.info("Market Data App exiting.")
