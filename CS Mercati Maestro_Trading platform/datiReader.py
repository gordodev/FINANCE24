import socket
import struct
import tkinter as tk
from threading import Thread
import queue

# Multicast setup
MCAST_GRP = '224.1.1.1'
MCAST_PORT = 5007

class MarketDataListener(Thread):
    def __init__(self, data_queue):
        super().__init__()
        self.data_queue = data_queue
        self.running = True

        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.sock.bind(('', MCAST_PORT))

        mreq = struct.pack("4sl", socket.inet_aton(MCAST_GRP), socket.INADDR_ANY)
        self.sock.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, mreq)

    def run(self):
        while self.running:
            data, _ = self.sock.recvfrom(1024)
            message = data.decode('utf-8')
            self.data_queue.put(message)

    def stop(self):
        self.running = False
        self.sock.close()

class MarketDataApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Market Data Feed")
        
        self.data_queue = queue.Queue()

        self.listener = MarketDataListener(self.data_queue)
        self.listener.start()

        self.frame = tk.Frame(root)
        self.frame.pack(fill=tk.BOTH, expand=True)

        self.label = tk.Label(self.frame, text="Market Data Feed", font=("Helvetica", 16))
        self.label.pack(pady=10)

        self.text = tk.Text(self.frame, state='disabled', height=15, width=50)
        self.text.pack(padx=10, pady=10)

        self.update_data()

    def update_data(self):
        while not self.data_queue.empty():
            message = self.data_queue.get_nowait()
            self.text.configure(state='normal')
            self.text.insert(tk.END, message + '\n')
            self.text.configure(state='disabled')
            self.text.see(tk.END)
        self.root.after(1000, self.update_data)

    def on_closing(self):
        self.listener.stop()
        self.root.destroy()

if __name__ == "__main__":
    root = tk.Tk()
    app = MarketDataApp(root)
    root.protocol("WM_DELETE_WINDOW", app.on_closing)
    root.mainloop()
