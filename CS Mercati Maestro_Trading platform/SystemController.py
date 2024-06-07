import tkinter as tk
from tkinter import messagebox
import os
import subprocess
import signal
import time
import psutil
import logging
import threading
import socket

"""
Platform Controller
--------------------
This script provides a GUI to start and shut down the trading platform. It includes two buttons:
- Start (green): Starts all trading platform components.
- Stop (red): Stops all trading platform components.

The script verifies the running status of the platform and confirms user actions.
"""

# Configure logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

# Define the base directory
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Paths to the scripts for each app
MARKET_DATA_APP = os.path.join(BASE_DIR, 'dati', 'dati.py')
TRADING_APP = os.path.join(BASE_DIR, 'maestro.py')  # Trading App is in the same directory as this controller script
ORDER_ROUTER_APP = os.path.join(BASE_DIR, 'SOR', 'SOR.py')
FIX_ENGINE_APP = os.path.join(BASE_DIR, 'FIX', 'FIX.py')
MARKET_SIMULATOR_APP = os.path.join(BASE_DIR, 'SIM', 'marketsimulator.py')

# List of all app scripts
APPS = [MARKET_DATA_APP, TRADING_APP, ORDER_ROUTER_APP, FIX_ENGINE_APP, MARKET_SIMULATOR_APP]

# Track subprocesses
processes = []

class PlatformController(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Trading Platform Controller")
        self.geometry("500x400")
        
        self.status_label = tk.Label(self, text="Status: Idle", font=("Helvetica", 14))
        self.status_label.pack(pady=20)
        
        self.details_text = tk.Text(self, height=10, width=60, state='disabled')
        self.details_text.pack(pady=10)
        
        self.start_button = tk.Button(self, text="Start", bg="green", command=self.start_platform, width=10)
        self.start_button.pack(pady=10)
        
        self.stop_button = tk.Button(self, text="Stop", bg="red", command=self.stop_platform, width=10)
        self.stop_button.pack(pady=10)
        
        self.protocol("WM_DELETE_WINDOW", self.on_closing)
    
    def update_status(self, status):
        self.status_label.config(text=f"Status: {status}")

    def append_text(self, text):
        self.details_text.config(state='normal')
        self.details_text.insert(tk.END, text + '\n')
        self.details_text.config(state='disabled')
        self.details_text.yview(tk.END)

    def start_platform(self):
        if self.is_running():
            if messagebox.askyesno("Platform Running", "The platform is already running. Do you want to restart it?"):
                self.stop_platform()
                self.start_apps_threaded()
            else:
                return
        else:
            self.start_apps_threaded()

    def start_apps_threaded(self):
        threading.Thread(target=self.start_apps).start()
    
    def stop_platform(self):
        if not self.is_running():
            messagebox.showerror("Error", "The platform is not running.")
            return
        self.stop_apps()
    
    def start_apps(self):
        self.update_status("Starting...")
        self.status_label.config(bg="blue")
        self.update()
        
        for app in APPS:
            app_name = os.path.basename(app)
            logging.debug(f"Starting {app_name}")
            self.append_text(f"Starting {app_name}")
            process = subprocess.Popen(['python', app])
            processes.append(process)
            
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
        
        # Wait and verify if all processes are running
        time.sleep(5)
        if all(process.poll() is None for process in processes):
            self.status_label.config(bg="green")
            self.update_status("Running")
        else:
            self.status_label.config(bg="red")
            self.update_status("Failed to Start")
            self.stop_apps()

    def get_network_info(self, pid):
        connections = psutil.net_connections(kind='inet')
        for conn in connections:
            if conn.pid == pid:
                laddr = f"{conn.laddr.ip}:{conn.laddr.port}"
                raddr = f"{conn.raddr.ip}:{conn.raddr.port}" if conn.raddr else "None"
                return f"Local address: {laddr}, Remote address: {raddr}"
        return "No network info available"
    
    def stop_apps(self):
        self.update_status("Stopping...")
        self.status_label.config(bg="blue")
        self.update()
        
        for process in processes:
            if process.poll() is None:
                os.kill(process.pid, signal.SIGTERM)
                logging.debug(f"Stopped {process.pid}")
                self.append_text(f"Stopped {process.pid}")
        
        processes.clear()
        self.status_label.config(bg="red")
        self.update_status("Stopped")
    
    def is_running(self):
        return any(process.poll() is None for process in processes)
    
    def on_closing(self):
        if self.is_running():
            self.stop_apps()
        self.destroy()

if __name__ == "__main__":
    app = PlatformController()
    app.mainloop()
