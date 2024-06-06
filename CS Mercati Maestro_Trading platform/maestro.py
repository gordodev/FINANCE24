import socket
import struct
import threading
import logging
import os
import sqlite3
import signal
import tkinter as tk
from tkinter import ttk
import time

# Configuration
MULTICAST_GROUP = '224.1.1.1'
MULTICAST_PORT = 5007
TCP_ORDER_ROUTER_HOST = 'localhost'
TCP_ORDER_ROUTER_PORT = 5008
LOG_DIR = 'logs'
LOG_FILE = f"{LOG_DIR}/trading{time.strftime('%y%m%d%H%M%S')}.log"
DB_FILE = 'orders.db'

# Ensure log directory exists
os.makedirs(LOG_DIR, exist_ok=True)

# Logging configuration
logging.basicConfig(filename=LOG_FILE, level=logging.DEBUG, format='%(asctime)s %(message)s')
logging.debug('Trading App started.')

# SQLite setup
conn = sqlite3.connect(DB_FILE)
cursor = conn.cursor()
cursor.execute('''CREATE TABLE IF NOT EXISTS orders (id INTEGER PRIMARY KEY, order_text TEXT)''')
conn.commit()

# Global variable for GUI elements
status_lights = {}

def listen_market_data():
    """Listen to market data multicast messages and log them."""
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sock.bind(('', MULTICAST_PORT))
    mreq = struct.pack('4sl', socket.inet_aton(MULTICAST_GROUP), socket.INADDR_ANY)
    sock.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, mreq)

    while True:
        data, _ = sock.recvfrom(1024)
        message = data.decode('utf-8')
        logging.debug(f'Received market data: {message}')
        process_market_data(message)

def process_market_data(message):
    """Process received market data and send orders."""
    order = f'Order for {message}'
    logging.debug(f'Processing market data, generated order: {order}')
    send_order(order)
    cursor.execute('INSERT INTO orders (order_text) VALUES (?)', (order,))
    conn.commit()

def send_order(order):
    """Send order to the Order Router via TCP."""
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.connect((TCP_ORDER_ROUTER_HOST, TCP_ORDER_ROUTER_PORT))
            s.sendall(order.encode('utf-8'))
            logging.debug(f'Sent order to Order Router: {order}')
    except Exception as e:
        logging.error(f'Error sending order: {e}')

def handle_exit(signum, frame):
    """Handle exit signals for graceful shutdown."""
    logging.debug('Trading App shutting down.')
    conn.close()
    exit(0)

# Signal handling for graceful shutdown
signal.signal(signal.SIGINT, handle_exit)
signal.signal(signal.SIGTERM, handle_exit)

def create_order_button(root, color, order_text):
    """Create a colored button to send orders."""
    button = tk.Button(root, text=color.capitalize(), bg=color, activebackground=color, command=lambda: send_order_action(order_text, button))
    button.config(width=10, height=5)
    return button

def send_order_action(order_text, button):
    """Animate button and send order."""
    button.config(relief=tk.SUNKEN)
    root.after(100, lambda: button.config(relief=tk.RAISED))
    send_order(order_text)

def create_status_light(frame, app_name):
    """Create a status light indicator."""
    canvas = tk.Canvas(frame, width=20, height=20, bg='grey')
    canvas.create_oval(5, 5, 15, 15, fill='grey', tags=app_name)
    canvas.pack(side=tk.LEFT, padx=5)
    status_lights[app_name] = canvas

def check_app_status(host, port, app_name):
    """Check if the app is running and update the status light."""
    while True:
        try:
            with socket.create_connection((host, port), timeout=1):
                status_lights[app_name].itemconfig(app_name, fill='green')
        except Exception:
            status_lights[app_name].itemconfig(app_name, fill='grey')
        time.sleep(5)

def start_gui():
    """Start the tkinter GUI."""
    global root
    root = tk.Tk()
    root.title("Trading App")

    button_frame = tk.Frame(root)
    button_frame.pack(pady=10)

    red_button = create_order_button(button_frame, 'red', 'Order for red')
    red_button.pack(side=tk.LEFT, padx=5)
    blue_button = create_order_button(button_frame, 'blue', 'Order for blue')
    blue_button.pack(side=tk.LEFT, padx=5)

    status_frame = tk.Frame(root)
    status_frame.pack(pady=10, side=tk.TOP, anchor=tk.NE)

    create_status_light(status_frame, 'Market Data')
    create_status_light(status_frame, 'Order Router')
    create_status_light(status_frame, 'FIX Engine')
    create_status_light(status_frame, 'Market Simulator')

    root.geometry("400x200")
    root.mainloop()

if __name__ == "__main__":
    threading.Thread(target=listen_market_data).start()
    threading.Thread(target=check_app_status, args=('localhost', 5007, 'Market Data')).start()
    threading.Thread(target=check_app_status, args=('localhost', 5008, 'Order Router')).start()
    threading.Thread(target=check_app_status, args=('localhost', 5009, 'FIX Engine')).start()
    threading.Thread(target=check_app_status, args=('localhost', 5010, 'Market Simulator')).start()
    start_gui()
