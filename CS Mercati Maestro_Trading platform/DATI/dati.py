# market_data_server.py
import socket
import threading
import time
import random

def handle_client(client_socket):
    while True:
        data = str(random.randint(0, 1))
        client_socket.send(data.encode())
        time.sleep(random.uniform(0.5, 2))  # Random interval between 0.5 to 2 seconds

def main():
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind(('0.0.0.0', 9999))
    server.listen(5)
    print("Market Data Server started on port 9999")

    while True:
        client_socket, addr = server.accept()
        print(f"Accepted connection from {addr}")
        client_handler = threading.Thread(target=handle_client, args=(client_socket,))
        client_handler.start()

if __name__ == "__main__":
    main()
