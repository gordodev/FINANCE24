import socket
import logging
import os
import signal

# Configuration
TCP_ORDER_ROUTER_HOST = 'localhost'
TCP_ORDER_ROUTER_PORT = 5009
TCP_MARKET_SIMULATOR_HOST = 'localhost'
TCP_MARKET_SIMULATOR_PORT = 5010
LOG_DIR = 'logs'
LOG_FILE = f"{LOG_DIR}/fixengine{time.strftime('%y%m%d%H%M%S')}.log"

# Ensure log directory exists
os.makedirs(LOG_DIR, exist_ok=True)

# Logging configuration
logging.basicConfig(filename=LOG_FILE, level=logging.DEBUG, format='%(asctime)s %(message)s')
logging.debug('FIX Engine App started.')

def handle_order(conn, addr):
    """Handle incoming orders from the Order Router and forward them to the Market Simulator."""
    with conn:
        order = conn.recv(1024).decode('utf-8')
        logging.debug(f'Received order from Order Router: {order}')
        send_to_market_simulator(order)

def send_to_market_simulator(order):
    """Send the received order to the Market Simulator."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.connect((TCP_MARKET_SIMULATOR_HOST, TCP_MARKET_SIMULATOR_PORT))
        s.sendall(order.encode('utf-8'))
        logging.debug(f'Sent order to Market Simulator: {order}')

def start_server():
    """Start the TCP server to listen for orders from the Order Router."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind((TCP_ORDER_ROUTER_HOST, TCP_ORDER_ROUTER_PORT))
        s.listen()
        logging.debug(f'FIX Engine listening on {TCP_ORDER_ROUTER_HOST}:{TCP_ORDER_ROUTER_PORT}')
        while True:
            conn, addr = s.accept()
            logging.debug(f'Connection from {addr}')
            handle_order(conn, addr)

def handle_exit(signum, frame):
    """Handle exit signals for graceful shutdown."""
    logging.debug('FIX Engine App shutting down.')
    exit(0)

# Signal handling for graceful shutdown
signal.signal(signal.SIGINT, handle_exit)
signal.signal(signal.SIGTERM, handle_exit)

if __name__ == "__main__":
    start_server()
