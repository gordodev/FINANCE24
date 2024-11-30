import tkinter as tk
from tkinter import ttk
import logging
import random

# Setting up DEBUG level logging
logging.basicConfig(level=logging.DEBUG)

class TradingApp(tk.Tk):
    def __init__(self):
        super().__init__()
        
        self.title("Trading App")
        self.geometry("600x400")
        self.configure(bg='#f5f5f5')
        
        # Create Buttons
        self.create_buttons()
        
        # Create Status Lights
        self.create_status_lights()
        
        # Create Status Bar
        self.create_status_bar()
        
        # Set initial status
        self.update_status("Application started")
        
        # Simulate status checks
        self.after(1000, self.simulate_status_checks)
    
    def create_buttons(self):
        frame = tk.Frame(self, bg='#f5f5f5')
        frame.pack(pady=50)
        
        blue_button = tk.Button(frame, text="Blue", command=lambda: self.send_trade("Blue"), bg='#1E90FF', fg='white', font=('Helvetica', 16), width=10, height=2)
        blue_button.pack(side=tk.LEFT, padx=20)
        
        red_button = tk.Button(frame, text="Red", command=lambda: self.send_trade("Red"), bg='#FF4500', fg='white', font=('Helvetica', 16), width=10, height=2)
        red_button.pack(side=tk.LEFT, padx=20)
    
    def create_status_lights(self):
        self.status_lights = {}
        frame = tk.Frame(self, bg='#f5f5f5')
        frame.pack(pady=10, anchor='ne')
        
        apps = ["FIX", "SOR", "Market Data", "Market Simulator"]
        for app in apps:
            light_frame = tk.Frame(frame, bg='#f5f5f5', padx=5, pady=5)
            light_frame.pack(side=tk.LEFT)
            self.status_lights[app] = tk.Label(light_frame, text=app, bg='grey', fg='white', width=12, height=2, font=('Helvetica', 10))
            self.status_lights[app].pack(side=tk.TOP)
    
    def create_status_bar(self):
        self.status_var = tk.StringVar()
        self.status_bar = tk.Label(self, textvariable=self.status_var, bd=1, relief=tk.SUNKEN, anchor=tk.W, bg='white')
        self.status_bar.pack(side=tk.BOTTOM, fill=tk.X)
    
    def send_trade(self, trade_type):
        logging.debug(f"Trade sent: {trade_type}")
        self.update_status(f"Trade sent: {trade_type}")
    
    def update_status(self, message):
        self.status_var.set(message)
        logging.debug(message)
    
    def simulate_status_checks(self):
        # Simulate status checks and update lights
        for app in self.status_lights:
            status = random.choice(["green", "red"])
            self.status_lights[app].configure(bg=status)
        
        self.after(5000, self.simulate_status_checks)

if __name__ == "__main__":
    app = TradingApp()
    app.mainloop()
