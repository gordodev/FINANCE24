import socket
import struct
import logging
import os
import tkinter as tk
from tkinter import messagebox
import threading
import time
import queue

# Logging setup
log_dir = "logs"
if not os.path.exists(log_dir):
    os.makedirs(log_dir)
logging.basicConfig(filename=os.path.join(log_dir, f'trading_test_{time.strftime("%y%m%d%H%M%S")}.log'),
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
            except Exception as e:
                logging.error(f"Error receiving market data message: {e}")
                self.update_status_callback("red")  # Update status light to red on error

    def stop(self):
        self.running = False
        try:
            self.sock.close()
            logging.info("MarketDataListener stopped")
        except Exception as e:
            logging.error(f"Error closing MarketDataListener socket: {e}")

class MarketDataTestApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Market Data Test App")
        self.root.geometry("800x600")
        self.data_queue = queue.Queue()

        # Initialize the MarketDataListener
        logging.debug("Starting MarketDataListener")
        self.listener = MarketDataListener(self.data_queue, self.schedule_update_status_bar)
        self.listener.start()

        # Create and layout the widgets
        self.create_widgets()

        # Start the market data processing
        self.root.after(1000, self.update_market_data)
        self.check_for_data()

    def create_widgets(self):
        # Top bar
        self.top_bar = tk.Frame(self.root, height=20, bg="red")
        self.top_bar.pack(fill=tk.X)

        # Middle frame for market data display
        self.middle_frame = tk.Frame(self.root)
        self.middle_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        self.market_data_display = tk.Label(self.middle_frame, text="Waiting for Market Data...", width=30, height=5, bg="#001f3f", fg="#add8e6", font=("Arial", 18, "bold"))
        self.market_data_display.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

    def update_market_data(self):
        logging.debug("Updating market data display")
        try:
            while not self.data_queue.empty():
                message, source_ip, source_port = self.data_queue.get_nowait()
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

    def schedule_update_status_bar(self, color):
        logging.debug(f"Scheduling update for status bar to {color}")
        self.root.after(0, self.update_status_bar, color)

    def update_status_bar(self, color):
        logging.debug(f"Updating status bar to {color}")
        try:
            self.top_bar.config(bg=color)
        except Exception as e:
            logging.error(f"Error updating status bar: {e}")
            messagebox.showerror("Error", f"Exception occurred: {e}")

    def check_for_data(self):
        if self.data_queue.empty():
            self.schedule_update_status_bar("red")
        else:
            self.schedule_update_status_bar("green")
        self.root.after(2000, self.check_for_data)

    def on_closing(self):
        logging.debug("Stopping MarketDataListener and closing app")
        self.listener.stop()
        self.root.destroy()

if __name__ == "__main__":
    try:
        logging.debug("Starting Market Data Test App")
        root = tk.Tk()
        app = MarketDataTestApp(root)
        root.protocol("WM_DELETE_WINDOW", app.on_closing)
        root.mainloop()
    except Exception as e:
        logging.error(f"Exception occurred: {e}")
        messagebox.showerror("Error", f"Exception occurred: {e}")
