#!/usr/bin/python3
import tkinter as tk
from tkinter import messagebox
import os
import subprocess
import signal
import time
import psutil
import logging
import threading

"""
Platform Controller
--------------------
This script provides a GUI to start and shut down the trading platform. It includes two buttons:
- Start (green): Starts all trading platform components.
- Stop (red): Stops all trading platform components.

The script verifies the running status of the platform and confirms user actions.
"""

# Define the base directory
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Create logs directory if it doesn't exist
LOG_DIR = os.path.join(BASE_DIR, 'logs')
os.makedirs(LOG_DIR, exist_ok=True)

# Configure logging
LOG_FILE = os.path.join(LOG_DIR, 'platform_controller.log')
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s', filename=LOG_FILE, filemode='a')

# Paths to the scripts for each app
MARKET_DATA_APP = os.path.join(BASE_DIR, 'dati', 'dati.py')
TRADING_APP = os.path.join(BASE_DIR, 'maestro.py')  # Trading App is in the same directory as this controller script
ORDER_ROUTER_APP = os.path.join(BASE_DIR, 'sor', 'sor.py')
FIX_ENGINE_APP = os.path.join(BASE_DIR, 'fix', 'fix.py')
MARKET_SIMULATOR_APP = os.path.join(BASE_DIR, 'sim', 'marketsimulator.py')

# List of all app scripts with their names
APPS = {
        "MARKET_DATA": MARKET_DATA_APP,
        "TRADING": TRADING_APP,
        "ORDER_ROUTER": ORDER_ROUTER_APP,
        "FIX_ENGINE": FIX_ENGINE_APP,
        "MARKET_SIMULATOR": MARKET_SIMULATOR_APP
        }

# Track subprocesses
processes = {}

class PlatformController(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Trading Platform Controller")
        self.geometry("600x500")

        self.status_label = tk.Label(self, text="Status: Idle", font=("Helvetica", 14))
        self.status_label.pack(pady=20)

        self.details_text = tk.Text(self, height=15, width=70, state='disabled')
        self.details_text.pack(pady=10)

        self.start_button = tk.Button(self, text="Start", bg="green", command=self.start_platform, width=10)
        self.start_button.pack(pady=10)

        self.stop_button = tk.Button(self, text="Stop", bg="red", command=self.stop_platform, width=10)
        self.stop_button.pack(pady=10)

        self.protocol("WM_DELETE_WINDOW", self.on_closing)

        # Tags for text formatting
        self.details_text.tag_configure('header', background='black', foreground='white', font=('Helvetica', 12, 'bold'))
        self.details_text.tag_configure('details', background='white', foreground='black', font=('Helvetica', 10))

        # Thread to monitor the status of apps
        self.monitor_thread = None
        self.monitoring = False

    def update_status(self, status):
        """Update the status label in the GUI."""
        self.status_label.config(text=f"Status: {status}")

    def append_text(self, text, is_header=False):
        """Append text to the details text box in the GUI."""
        self.details_text.config(state='normal')
        if is_header:
            self.details_text.insert(tk.END, text + '\n', ('header',))
        else:
            self.details_text.insert(tk.END, text + '\n', ('details',))
        self.details_text.config(state='disabled')
        self.details_text.yview(tk.END)

    def start_platform(self):
        """Handle the start platform button click."""
        if self.is_running():
            if messagebox.askyesno("Platform Running", "The platform is already running. Do you want to restart it?"):
                self.stop_platform()
                self.start_apps_threaded()
            else:
                return
        else:
            self.start_apps_threaded()

    def start_apps_threaded(self):
        """Start the apps in a new thread to prevent blocking the GUI."""
        threading.Thread(target=self.start_apps).start()

    def stop_platform(self):
        """Handle the stop platform button click."""
        if not self.is_running():
            messagebox.showerror("Error", "The platform is not running.")
            return
        self.stop_apps()

    def start_apps(self):
        """Start all trading platform apps."""
        self.update_status("Starting...")
        self.status_label.config(bg="blue")
        self.update()

        all_started = True

        for app_name, app_path in APPS.items():
            logging.debug(f"Starting {app_name}")
            self.append_text(f"Starting {app_name}")
            process = subprocess.Popen(['python3', app_path])
            processes[app_name] = process

            # Pause between starting each app
            time.sleep(2)

            # Check if process is running and get resource usage
            if process.poll() is None:
                proc_info = psutil.Process(process.pid)
                cpu_usage = proc_info.cpu_percent(interval=1)
                mem_info = proc_info.memory_info()
                ram_usage = mem_info.rss / (1024 ** 2)  # Convert bytes to MB

                net_info = self.get_network_info(process.pid)

                log_message = f"{app_name} running, using {cpu_usage}% CPU and {ram_usage:.2f}MB RAM. Network details: {net_info}"
                logging.debug(log_message)
                self.append_text(log_message)
            else:
                log_message = f"Failed to start {app_name}"
                logging.error(log_message)
                self.append_text(log_message)
                all_started = False
                messagebox.showerror("Error", f"Failed to start {app_name}")

        # Wait and verify if all processes are running
        time.sleep(5)
        if all(process.poll() is None for process in processes.values()):
            self.status_label.config(bg="green")
            self.update_status("Running")
            self.start_monitoring()
        else:
            self.status_label.config(bg="red")
            self.update_status("Failed to Start")
            if all_started:
                messagebox.showinfo("Information", "All apps started successfully.")
            else:
                messagebox.showwarning("Warning", "Some apps failed to start. Check logs for details.")

    def get_network_info(self, pid):
        """Get network information for a given process ID."""
        connections = psutil.net_connections(kind='inet')
        for conn in connections:
            if conn.pid == pid:
                laddr = f"{conn.laddr.ip}:{conn.laddr.port}"
                raddr = f"{conn.raddr.ip}:{conn.raddr.port}" if conn.raddr else "None"
                return f"{laddr}, Remote: {raddr}"
        return "No network info available"

    def stop_apps(self):
        """Stop all running trading platform apps."""
        self.update_status("Stopping...")
        self.status_label.config(bg="blue")
        self.update()

        for app_name, process in processes.items():
            if process.poll() is None:
                os.kill(process.pid, signal.SIGTERM)
                logging.debug(f"Stopped {app_name}")
                self.append_text(f"Stopped {app_name}")

        processes.clear()
        self.status_label.config(bg="red")
        self.update_status("Stopped")
        self.stop_monitoring()

    def is_running(self):
        """Check if any platform apps are currently running."""
        return any(process.poll() is None for process in processes.values())

    def on_closing(self):
        """Handle the closing event of the GUI."""
        if self.is_running():
            self.stop_apps()
        self.stop_monitoring()
        self.destroy()

    def start_monitoring(self):
        """Start the background thread for monitoring the app statuses."""
        self.monitoring = True
        self.monitor_thread = threading.Thread(target=self.monitor_status)
        self.monitor_thread.start()

    def stop_monitoring(self):
        """Stop the background thread for monitoring the app statuses."""
        self.monitoring = False
        if self.monitor_thread:
            self.monitor_thread.join()

    def monitor_status(self):
        """Monitor the status of the apps and update the GUI with timestamps."""
        while self.monitoring:
            for app_name, process in processes.items():
                if process.poll() is None:
                    proc_info = psutil.Process(process.pid)
                    cpu_usage = proc_info.cpu_percent(interval=1)
                    mem_info = proc_info.memory_info()
                    ram_usage = mem_info.rss / (1024 ** 2)  # Convert bytes to MB

                    net_info = self.get_network_info(process.pid)
                    timestamp = time.strftime("%Y-%m-%d %H:%M:%S")

                    header_message = f"{timestamp} - {app_name}"
                    details_message = (f"CPU: {cpu_usage}% | RAM: {ram_usage:.2f}MB | "
                                       f"NET: {net_info}")

                    logging.debug(header_message)
                    logging.debug(details_message)
                    self.append_text(header_message, is_header=True)
                    self.append_text(details_message)
            time.sleep(4)

if __name__ == "__main__":
    app = PlatformController()
    app.mainloop()
