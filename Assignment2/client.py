import socket
import threading

# Function to receive messages from server
def receive_messages(client_socket):
    while True:
        try:
            # Receive message from server
            message = client_socket.recv(1024).decode('utf-8')
            print(message)
        except Exception as e:
            print(f"Error: {e}")
            break

# Main function
def main():
    # Client configuration
    host = 'localhost'
    port = 8888

    # Create client socket
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client_socket.connect((host, port))

    # Receive username prompt from server
    username = input(client_socket.recv(1024).decode('utf-8'))

    # Send username to server
    client_socket.sendall(username.encode('utf-8'))

    # Start thread to receive messages from server
    receive_thread = threading.Thread(target=receive_messages, args=(client_socket,))
    receive_thread.start()

    # Send messages to server
    while True:
        message = input()
        client_socket.sendall(message.encode('utf-8'))

    client_socket.close()

if __name__ == "__main__":
    main()
