import socket
import threading

# Function to handle client connections
def handle_client(client_socket, clients, client_names):
    while True:
        try:
            # Receive message from client
            message = client_socket.recv(1024).decode('utf-8')
            if message:
                # Broadcast message to all clients
                for client in clients:
                    if client != client_socket:
                        client.sendall(f"[{client_names[client_socket]}] {message}".encode('utf-8'))
        except Exception as e:
            print(f"Error: {e}")
            break

    # Remove client from list and close connection
    clients.remove(client_socket)
    client_socket.close()
    del client_names[client_socket]

# Main function
def main():
    # Server configuration
    host = 'localhost'
    port = 8888

    # Create server socket
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.bind((host, port))
    server_socket.listen(5)

    print(f"[*] Listening on {host}:{port}")

    clients = []
    client_names = {}

    while True:
        # Accept client connection
        client_socket, addr = server_socket.accept()
        print(f"[*] Accepted connection from {addr[0]}:{addr[1]}")

        # Prompt client for username
        client_socket.sendall("Enter your name: ".encode('utf-8'))
        username = client_socket.recv(1024).decode('utf-8').strip()
        client_names[client_socket] = username

        # Add client to list
        clients.append(client_socket)

        # Create thread to handle client
        client_thread = threading.Thread(target=handle_client, args=(client_socket, clients, client_names))
        client_thread.start()

    server_socket.close()

if __name__ == "__main__":
    main()
