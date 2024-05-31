# trading_server.py
import socket
import threading
import datetime

def handle_client(client_socket, client_address):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as fix_socket:
        fix_socket.connect(('localhost', 10001))  # Update IP address to that of Server 1
        while True:
            message = client_socket.recv(1024).decode()
            if message:
                log_order(client_address, message)
                fix_socket.send(message.encode())

def log_order(client_address, message):
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")
    with open("trading_server_log.txt", "a") as log_file:
        log_file.write(f"{timestamp} - {client_address} - {message}\n")

def main():
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind(('0.0.0.0', 10002))
    server.listen(5)
    print("Trading Server started on port 10002")

    while True:
        client_socket, client_address = server.accept()
        print(f"Accepted connection from {client_address}")
        client_handler = threading.Thread(target=handle_client, args=(client_socket, client_address))
        client_handler.start()

if __name__ == "__main__":
    main()

