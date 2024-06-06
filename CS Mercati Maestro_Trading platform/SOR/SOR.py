import socket
import logging
import os
import signal

# Configuration
TCP_TRADING_APP_HOST = 'localhost'
TCP_TRADING_APP_PORT = 5008
TCP_FIX_ENGINE_HOST = 'localhost'
TCP_FIX_ENGINE_PORT = 5009
LOG_DIR = 'logs'
LOG_FILE = f"{LOG_DIR}/orderrouter{time.strftime('%y%m%d%H%M%S')}.log"

# Ensure log directory exists
os.makedirs(LOG_DIR, exist_ok=True)

# Logging configuration
logging.basicConfig(filename=LOG_FILE, level=logging.DEBUG, format='%(asctime)s %(message)s')
logging.debug('Order Router App started.')

def handle_order(conn, addr):
    """Handle incoming orders from the Trading App and forward them to the FIX Engine."""
    with conn:
        order = conn.recv(1024).decode('utf-8')
        logging.debug(f'Received order from Trading App: {order}')
        send_to_fix_engine(order)

def send_to_fix_engine(order):
    """Send the received order to the FIX Engine."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.connect((TCP_FIX_ENGINE_HOST, TCP_FIX_ENGINE_PORT))
        s.sendall(order.encode('utf-8'))
        logging.debug(f'Sent order to FIX Engine: {order}')

def start_server():
    """Start the TCP server to listen for orders from the Trading App."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind((TCP_TRADING_APP_HOST, TCP_TRADING_APP_PORT))
        s.listen()
        logging.debug(f'Order Router listening on {TCP_TRADING_APP_HOST}:{TCP_TRADING_APP_PORT}')
        while True:
            conn, addr = s.accept()
            logging.debug(f'Connection from {addr}')
            handle_order(conn, addr)

def handle_exit(signum, frame):
    """Handle exit signals for graceful shutdown."""
    logging.debug('Order Router App shutting down.')
    exit(0)

# Signal handling for graceful shutdown
signal.signal(signal.SIGINT, handle_exit)
signal.signal(signal.SIGTERM, handle_exit)

if __name__ == "__main__":
    start_server()
