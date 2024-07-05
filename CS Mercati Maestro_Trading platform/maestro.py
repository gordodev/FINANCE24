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

commit issue on 7/5/24
"""

# Logging setup
log_dir = "logs"
if not os.path.exists(log_dir):
    os.makedirs(log_dir)
logging.basicConfig(filename=os.path.join(log_dir, f'trading_{time.strftime("%y%m%d%H%M%S")}.log'),
                    level=logging.DEBUG,
                    format='%(asctime)s %(levelname)s %(message)s')

# Multicast setup
MCAST_GRP = '224.1.1.1'
MCAST_PORT = 5007

class MarketDataListener(threading.Thread):
    def __init__(self, data_queue, update_status_callback):
        super().__init__()
        self.data_queue = data_queue
        self.update_status_callback = update_status_callback
        self.running = True

        logging.debug("Initializing MarketDataListener")

        # Set up the socket for receiving multicast data
        try:
            self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
            self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.sock.bind(('', MCAST_PORT))
            logging.info(f"Socket bound to ('', {MCAST_PORT})")

            # Join the multicast group
            mreq = struct.pack("4sl", socket.inet_aton(MCAST_GRP), socket.INADDR_ANY)
            self.sock.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, mreq)
            logging.info(f"MarketDataListener joined multicast group {MCAST_GRP} on port {MCAST_PORT}")
            
            # Set socket timeout
            self.sock.settimeout(1)  # 1 second timeout
        except Exception as e:
            logging.error(f"Failed to initialize MarketDataListener: {e}")

    def run(self):
        logging.debug("MarketDataListener thread started")
        while self.running:
            try:
                # Receive data from the multicast group
                data, addr = self.sock.recvfrom(1024)
                source_ip, source_port = addr
                message = data.decode('utf-8')
                self.data_queue.put((message, source_ip, source_port))
                logging.debug(f"Received market data message from {source_ip}:{source_port}: {message}")
                self.update_status_callback("green")  # Update status light to green on successful data reception
            except socket.timeout:
                # This is normal, just continue
                continue
            except Exception as e:
                logging.error(f"Error receiving market data message: {e}")
                self.update_status_callback("red")  # Update status light to red on error
                time.sleep(1)  # Avoid tight loop on persistent errors

    def stop(self):
        self.running = False
        try:
            self.sock.close()
            logging.info("MarketDataListener stopped")
        except Exception as e:
            logging.error(f"Error closing MarketDataListener socket: {e}")

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
        self.status_update_queue = queue.Queue()

        # Initialize the MarketDataListener
        logging.debug("Starting MarketDataListener")
        self.listener = MarketDataListener(self.data_queue, self.schedule_update_market_data_status)
        self.listener.start()

        # Create and layout the widgets
        self.create_widgets()

        # Start the status light updates and market data processing
        self.update_status_lights()
        self.root.after(100, self.process_status_updates)
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
        logging.debug("Updating market data display")
        try:
            while not self.data_queue.empty():
                message, source_ip, source_port = self.data_queue.get_nowait()
                logging.debug(f"Processing message: {message} from {source_ip}:{source_port}")
                self.root.after(0, self.log_market_data, message, source_ip, source_port)
            self.root.after(1000, self.update_market_data)  # Keep checking for new data
        except Exception as e:
            logging.error(f"Error in update_market_data: {e}")
            messagebox.showerror("Error", f"Exception occurred: {e}")

    def log_market_data(self, message, source_ip, source_port):
        # Log market data messages with a timestamp and source details
        timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
        log_message = f"{timestamp} - {message} from {source_ip}:{source_port}"
        logging.info(log_message)
        self.market_data_display.config(text=log_message, bg="#001f3f", fg="#add8e6", font=("Arial", 18, "bold"))

    def send_order(self, color):
        # Send an order to the Order Router via TCP
        logging.debug(f"Preparing to send order: {color}")
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                destination_ip = 'localhost'
                destination_port = 5008
                logging.info(f"Connecting to Order Router at {destination_ip}:{destination_port}")
                s.connect((destination_ip, destination_port))
                order = f'order {color}'
                s.sendall(order.encode('utf-8'))
                logging.debug(f'Sent order to {destination_ip}:{destination_port}: {order}')
                self.status_bar.config(text=f"Status: Sent order {color}")
        except ConnectionRefusedError:
            messagebox.showerror("Error", "Order Router is down. Cannot send order.")
            logging.error("Order Router is down. Cannot send order.")
            self.status_bar.config(text="Status: Order Router is down. Cannot send order.")
        except Exception as e:
            logging.error(f"Error sending order: {e}")
            messagebox.showerror("Error", f"Exception occurred while sending order: {e}")

    def update_status_lights(self):
        logging.debug("Updating status lights")
        try:
            self.check_dependencies()
            self.root.after(5000, self.update_status_lights)
        except Exception as e:
            logging.error(f"Error in update_status_lights: {e}")
            messagebox.showerror("Error", f"Exception occurred: {e}")

    def check_dependencies(self):
        logging.debug("Checking dependencies")
        # Check the status of various components and update the status lights
        components = {
            "OrderRouter": 5008,
            "FIXEngine": 5009,
            "MarketSimulator": 5010
        }
        for component, port in components.items():
            status = self.ping_component(port)
            color = "green" if status else "grey"
            logging.debug(f"Component {component} status: {'up' if status else 'down'}")
            self.root.after(0, self.status_lights[component].configure, {'bg': color})
        
        # Check the status of MarketData multicast reception
        market_data_status = self.check_market_data_multicast()
        color = "green" if market_data_status else "grey"
        logging.debug(f"MarketData component status: {'up' if market_data_status else 'down'}")
        self.root.after(0, self.status_lights["MarketData"].configure, {'bg': color})

    def check_market_data_multicast(self):
        logging.debug("Checking market data multicast")
        try:
            # Set up the socket for receiving multicast data
            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            sock.bind(('', MCAST_PORT))

            # Join the multicast group
            mreq = struct.pack("4sl", socket.inet_aton(MCAST_GRP), socket.INADDR_ANY)
            sock.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, mreq)

            # Attempt to receive data
            sock.settimeout(1)
            try:
                data, _ = sock.recvfrom(1024)
                logging.debug("Successfully received multicast data")
                return True
            except socket.timeout:
                logging.error("Failed to receive multicast data within the timeout period")
                return False
            finally:
                sock.close()
        except Exception as e:
            logging.error(f"Error checking market data multicast: {e}")
            return False

    def schedule_update_market_data_status(self, color):
        logging.debug(f"Scheduling update for Market Data status light to {color}")
        self.status_update_queue.put(color)

    def process_status_updates(self):
        try:
            while not self.status_update_queue.empty():
                color = self.status_update_queue.get_nowait()
                self.update_market_data_status(color)
        except queue.Empty:
            pass
        finally:
            self.root.after(100, self.process_status_updates)

    def update_market_data_status(self, color):
        logging.debug(f"Updating Market Data status light to {color}")
        try:
            self.status_lights["MarketData"].configure(bg=color)
        except Exception as e:
            logging.error(f"Error updating market data status light: {e}")
            messagebox.showerror("Error", f"Exception occurred: {e}")

    def ping_component(self, port):
        logging.debug(f"Pinging component on port {port}")
        # Check if a component is reachable via TCP
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                destination_ip = 'localhost'
                logging.info(f"Trying to connect to {destination_ip}:{port}")
                s.connect((destination_ip, port))
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
        logging.debug("Starting TradingApp")
        root = tk.Tk()
        app = TradingApp(root)
        root.protocol("WM_DELETE_WINDOW", lambda: (app.listener.stop(), root.destroy()))
        root.mainloop()
    except Exception as e:
        logging.error(f"Exception occurred: {e}")
        messagebox.showerror("Error", f"Exception occurred: {e}")