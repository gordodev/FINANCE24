import socket
import struct
import logging
import os
import tkinter as tk
from tkinter import messagebox
import sqlite3
import signal
import sys
import threading
import time

"""
Trading Front End App
---------------------
This application listens to the Market Data App for "blue" or "red" messages, logs received messages, 
sends orders to the Order Router, and logs orders to a database.

- Receiving: Multicast from 224.1.1.1 on port 5007.
- Sending: TCP to Order Router on localhost:5008.
- Dependencies: SQLite3, tkinter
"""

# Logging setup
log_dir = "logs"
if not os.path.exists(log_dir):
    os.makedirs(log_dir)
logging.basicConfig(filename=os.path.join(log_dir, f'trading_{time.strftime("%y%m%d%H%M%S")}.log'), 
                    level=logging.DEBUG, 
                    format='%(asctime)s %(message)s')

# Multicast setup
MCAST_GRP = '224.1.1.1'
MCAST_PORT = 5007

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
sock.bind(('', MCAST_PORT))

mreq = struct.pack("4sl", socket.inet_aton(MCAST_GRP), socket.INADDR_ANY)
sock.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, mreq)

# Database setup
conn = sqlite3.connect('orders.db')
c = conn.cursor()
c.execute('''CREATE TABLE IF NOT EXISTS orders (timestamp TEXT, "order" TEXT)''')
conn.commit()

def signal_handler(sig, frame):
    logging.info("Trading App interrupted and exiting gracefully.")
    conn.close()
    sys.exit(0)

signal.signal(signal.SIGINT, signal_handler)

class TradingApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Trading App")
        self.create_widgets()
        self.update_status_lights()
        self.listen_market_data()
        self.check_dependencies()

    def create_widgets(self):
        self.red_button = tk.Button(self.root, text="Red", bg="red", width=10, height=5, command=lambda: self.send_order("red"))
        self.red_button.grid(row=0, column=0, padx=10, pady=10)

        self.blue_button = tk.Button(self.root, text="Blue", bg="blue", width=10, height=5, command=lambda: self.send_order("blue"))
        self.blue_button.grid(row=0, column=1, padx=10, pady=10)

        self.status_lights = {
            "MarketData": tk.Canvas(self.root, width=20, height=20, bg="grey"),
            "OrderRouter": tk.Canvas(self.root, width=20, height=20, bg="grey"),
            "FIXEngine": tk.Canvas(self.root, width=20, height=20, bg="grey"),
            "MarketSimulator": tk.Canvas(self.root, width=20, height=20, bg="grey")
        }

        col = 2
        for component, light in self.status_lights.items():
            tk.Label(self.root, text=component).grid(row=0, column=col, padx=10, pady=10)
            light.grid(row=0, column=col+1, padx=10, pady=10)
            col += 2

    def listen_market_data(self):
        def listen():
            while True:
                data, _ = sock.recvfrom(1024)
                message = data.decode('utf-8')
                logging.debug(f'Received market data message: {message}')
                self.root.after(0, self.log_market_data, message)
        thread = threading.Thread(target=listen, daemon=True)
        thread.start()

    def log_market_data(self, message):
        timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
        c.execute('INSERT INTO orders (timestamp, "order") VALUES (?, ?)', (timestamp, message))
        conn.commit()

    def send_order(self, color):
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.connect(('localhost', 5008))
                order = f'order {color}'
                s.sendall(order.encode('utf-8'))
                logging.debug(f'Sent order: {order}')
        except ConnectionRefusedError:
            messagebox.showerror("Error", "Order Router is down. Cannot send order.")
            logging.error("Order Router is down. Cannot send order.")

    def update_status_lights(self):
        self.check_dependencies()
        self.root.after(5000, self.update_status_lights)

    def check_dependencies(self):
        components = {
            "OrderRouter": 5008,
            "FIXEngine": 5009,
            "MarketSimulator": 5010
        }
        for component, port in components.items():
            status = self.ping_component(port)
            color = "green" if status else "grey"
            self.status_lights[component].configure(bg=color)

    def ping_component(self, port):
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.connect(('localhost', port))
            return True
        except ConnectionRefusedError:
            return False

if __name__ == "__main__":
    root = tk.Tk()
    app = TradingApp(root)
    root.mainloop()
