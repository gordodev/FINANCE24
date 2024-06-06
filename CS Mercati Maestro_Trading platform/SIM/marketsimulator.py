import socket
import logging
import os
import signal

# Configuration
TCP_FIX_ENGINE_HOST = 'localhost'
TCP_FIX_ENGINE_PORT = 5010
LOG_DIR = 'logs'
LOG_FILE = f"{LOG_DIR}/marketsimulator{time.strftime('%y%m%d%H%M%S')}.log"

# Ensure log directory exists
os.makedirs(LOG_DIR, exist_ok=True)

# Logging configuration
logging.basicConfig(filename=LOG_FILE, level=logging.DEBUG, format='%(asctime)s %(message)s')
logging.debug('Market Simulator App started.')

fill_colors = ['red', 'blue']
fill_index = 0

def handle_order(conn, addr):
    """Handle incoming orders from the FIX Engine and send fill messages back."""
    global fill_index
    with conn:
        order = conn.recv(1024).decode('utf-8')
        logging.debug(f'Received order from FIX Engine: {order}')
        fill_message = f'fill 1 {fill_colors[fill_index]}'
        fill_index = (fill_index + 1) % len(fill_colors)
        send_fill_to_fix_engine(fill_message)

def send_fill_to_fix_engine(fill_message):
    """Send the fill message back to the FIX Engine."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.connect((TCP_FIX_ENGINE_HOST, TCP_FIX_ENGINE_PORT))
        s.sendall(fill_message.encode('utf-8'))
        logging.debug(f'Sent fill message to FIX Engine: {fill_message}')

def start_server():
    """Start the TCP server to listen for orders from the FIX Engine."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind((TCP_FIX_ENGINE_HOST, TCP_FIX_ENGINE_PORT))
        s.listen()
        logging.debug(f'Market Simulator listening on {TCP_FIX_ENGINE_HOST}:{TCP_FIX_ENGINE_PORT}')
        while True:
            conn, addr = s.accept()
            logging.debug(f'Connection from {addr}')
            handle_order(conn, addr)

def handle_exit(signum, frame):
    """Handle exit signals for graceful shutdown."""
    logging.debug('Market Simulator App shutting down.')
    exit(0)

# Signal handling for graceful shutdown
signal.signal(signal.SIGINT, handle_exit)
signal.signal(signal.SIGTERM, handle_exit)

if __name__ == "__main__":
    start_server()
