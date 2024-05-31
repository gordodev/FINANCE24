# compliance_risk_server.py
import socket
import threading

def handle_client(client_socket):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as trading_socket:
        trading_socket.connect(('localhost', 10002))  # Connect to Trading Server
        while True:
            message = client_socket.recv(1024).decode()
            if message:
                color, quantity = message.split()
                quantity = int(quantity)
                if color in ['red', 'blue'] and quantity == 1:
                    response = "Order accepted"
                    trading_socket.send(message.encode())  # Forward to Trading Server
                else:
                    response = "Order rejected"
                client_socket.send(response.encode())

def main():
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind(('0.0.0.0', 10000))
    server.listen(5)
    print("Compliance and Risk Server started on port 10000")

    while True:
        client_socket, addr = server.accept()
        print(f"Accepted connection from {addr}")
        client_handler = threading.Thread(target=handle_client, args=(client_socket,))
        client_handler.start()

if __name__ == "__main__":
    main()
