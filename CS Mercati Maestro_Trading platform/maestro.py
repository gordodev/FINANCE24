import socket
import struct
import logging
import os
import tkinter as tk
from tkinter import messagebox
import signal
import sys
import threading
import time
import queue


"""
Trading Front End App
---------------------
This application listens to the Market Data App for "blue" or "red" messages, logs received messages, 
sends orders to the Order Router, and logs orders to a database.

- Receiving: Multicast from 224.1.1.1 on port 5007.
- Sending: TCP to Order Router on localhost:5008.
- Dependencies: SQLite3, tkinter

BUGS:

Not sending orders? I just see it recieving MD, but not sending anything. I see activity down stream, but how if nothing sent out?
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

class MarketDataListener(threading.Thread):
    def __init__(self, data_queue, update_status_callback):
        super().__init__()
        self.data_queue = data_queue
        self.update_status_callback = update_status_callback
        self.running = True

        # Set up the socket for receiving multicast data
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.sock.bind(('', MCAST_PORT))

        # Join the multicast group
        mreq = struct.pack("4sl", socket.inet_aton(MCAST_GRP), socket.INADDR_ANY)
        self.sock.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, mreq)
        logging.info("MarketDataListener initialized and joined multicast group")

    def run(self):
        while self.running:
            try:
                # Receive data from the multicast group
                data, _ = self.sock.recvfrom(1024)
                message = data.decode('utf-8')
                self.data_queue.put(message)
                logging.debug(f"Received market data message: {message}")
                self.update_status_callback("green")  # Update status light to green on successful data reception
            except Exception as e:
                logging.error(f"Error receiving market data message: {e}")
                self.update_status_callback("red")  # Update status light to red on error

    def stop(self):
        self.running = False
        self.sock.close()
        logging.info("MarketDataListener stopped")

def signal_handler(sig, frame):
    logging.info("Trading App interrupted and exiting gracefully.")
    sys.exit(0)

signal.signal(signal.SIGINT, signal_handler)

class TradingApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Trading App")
        self.root.geometry("800x600")
        self.data_queue = queue.Queue()

        # Initialize the MarketDataListener
        self.listener = MarketDataListener(self.data_queue, self.update_market_data_status)
        self.listener.start()

        # Create and layout the widgets
        self.create_widgets()

        # Start the status light updates and market data processing
        self.update_status_lights()
        self.root.after(2000, self.update_market_data)
        self.check_dependencies()

    def create_widgets(self):
        # Main frames
        self.top_frame = tk.Frame(self.root, bd=2, relief=tk.SOLID)
        self.top_frame.grid(row=0, column=0, columnspan=2, sticky="nsew", padx=10, pady=5)

        self.middle_frame = tk.Frame(self.root)
        self.middle_frame.grid(row=1, column=0, columnspan=2, sticky="nsew", padx=10, pady=5)

        self.empty_frame = tk.Frame(self.root)
        self.empty_frame.grid(row=2, column=0, columnspan=2, sticky="nsew", padx=10, pady=5)

        self.bottom_frame = tk.Frame(self.root, bd=1, relief=tk.SUNKEN)
        self.bottom_frame.grid(row=3, column=0, columnspan=2, sticky="nsew", padx=10, pady=5)

        self.status_bar = tk.Label(self.root, text="Status: Ready", bd=1, relief=tk.SUNKEN, anchor=tk.W)
        self.status_bar.grid(row=4, column=0, columnspan=2, sticky="nsew")

        # Top frame widgets
        self.red_button = tk.Button(self.top_frame, text="Red", bg="red", width=10, height=5, command=lambda: self.send_order("red"))
        self.red_button.pack(side=tk.LEFT, padx=10, pady=10)

        self.blue_button = tk.Button(self.top_frame, text="Blue", bg="blue", width=10, height=5, command=lambda: self.send_order("blue"))
        self.blue_button.pack(side=tk.LEFT, padx=10, pady=10)

        self.status_lights_frame = tk.Frame(self.top_frame, bd=2, relief=tk.SOLID)
        self.status_lights_frame.pack(side=tk.RIGHT, padx=10, pady=10)

        self.status_lights = {
            "MarketData": tk.Canvas(self.status_lights_frame, width=20, height=20, bg="grey"),
            "OrderRouter": tk.Canvas(self.status_lights_frame, width=20, height=20, bg="grey"),
            "FIXEngine": tk.Canvas(self.status_lights_frame, width=20, height=20, bg="grey"),
            "MarketSimulator": tk.Canvas(self.status_lights_frame, width=20, height=20, bg="grey")
        }

        row = 0
        for component, light in self.status_lights.items():
            tk.Label(self.status_lights_frame, text=component).grid(row=row, column=0, padx=10, pady=5)
            light.grid(row=row, column=1, padx=10, pady=5)
            row += 1

        # Middle frame widgets
        self.market_data_display = tk.Label(self.middle_frame, text="Loading Market Data", width=30, height=5, bg="#001f3f", fg="#add8e6", font=("Arial", 18, "bold"))
        self.market_data_display.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

    def update_market_data(self):
        try:
            if not self.data_queue.empty():
                message = self.data_queue.get_nowait()
                self.log_market_data(message)
            self.root.after(1000, self.update_market_data)  # Keep checking for new data
        except Exception as e:
            logging.error(f"Error in update_market_data: {e}")
            messagebox.showerror("Error", f"Exception occurred: {e}")

    def log_market_data(self, message):
        # Log market data messages with a timestamp
        timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
        log_message = f"{timestamp} - {message}"
        logging.info(log_message)
        self.market_data_display.config(text=log_message, bg="#001f3f", fg="#add8e6", font=("Arial", 18, "bold"))

    def send_order(self, color):
        # Send an order to the Order Router via TCP
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.connect(('localhost', 5008))
                order = f'order {color}'
                s.sendall(order.encode('utf-8'))
                logging.debug(f'Sent order: {order}')
                self.status_bar.config(text=f"Status: Sent order {color}")
        except ConnectionRefusedError:
            messagebox.showerror("Error", "Order Router is down. Cannot send order.")
            logging.error("Order Router is down. Cannot send order.")
            self.status_bar.config(text="Status: Order Router is down. Cannot send order.")
        except Exception as e:
            logging.error(f"Error sending order: {e}")
            messagebox.showerror("Error", f"Exception occurred while sending order: {e}")

    def update_status_lights(self):
        try:
            self.check_dependencies()
            self.root.after(5000, self.update_status_lights)
        except Exception as e:
            logging.error(f"Error in update_status_lights: {e}")
            messagebox.showerror("Error", f"Exception occurred: {e}")

    def check_dependencies(self):
        # Check the status of various components and update the status lights
        components = {
            "OrderRouter": 5008,
            "FIXEngine": 5009,
            "MarketSimulator": 5010
        }
        for component, port in components.items():
            status = self.ping_component(port)
            color = "green" if status else "grey"
            self.status_lights[component].configure(bg=color)

    def update_market_data_status(self, color):
        # Update the status light for market data
        try:
            logging.debug(f"Updating Market Data status light to {color}")
            self.status_lights["MarketData"].configure(bg=color)
        except Exception as e:
            logging.error(f"Error updating market data status light: {e}")
            messagebox.showerror("Error", f"Exception occurred: {e}")

    def ping_component(self, port):
        # Check if a component is reachable via TCP
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.connect(('localhost', port))
            logging.debug(f"Component on port {port} is up")
            return True
        except ConnectionRefusedError:
            logging.debug(f"Component on port {port} is down")
            return False
        except Exception as e:
            logging.error(f"Error pinging component on port {port}: {e}")
            return False

if __name__ == "__main__":
    try:
        root = tk.Tk()
        app = TradingApp(root)
        root.protocol("WM_DELETE_WINDOW", lambda: (app.listener.stop(), root.destroy()))
        root.mainloop()
    except Exception as e:
        logging.error(f"Exception occurred: {e}")
        messagebox.showerror("Error", f"Exception occurred: {e}")
