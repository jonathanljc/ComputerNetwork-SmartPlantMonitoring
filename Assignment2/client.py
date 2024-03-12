import socket
import threading

def receive_messages(client_socket, current_username):
    while True:
        try:
            message = client_socket.recv(1024).decode('utf-8')
            if message.startswith("[") and message.endswith(" joined]"):
                print(message)
            elif ':' in message:
                sender, message_body = message.split(':', 1)
                if sender != current_username:  # Check if sender is not the current client
                    if message_body.strip().startswith('@'):
                        recipient, message_body = message_body.strip().split(' ', 1)
                        if recipient == current_username:
                            print(message)
                    elif message.startswith(f"[To {current_username}]"):
                        print(message)
                    else:
                        print(message)
            else:
                print(message)
        except Exception as e:
            print(f"Error: {e}")
            break

def send_messages(client_socket, current_username):
    while True:
        message = input("Enter message (or type '@quit' to exit): ")
        if message == '@quit':
            client_socket.sendall(message.encode('utf-8'))
            client_socket.close()  # Close the client socket
            break
        elif message.startswith('@'):
            if message.strip() == "@names":
                client_socket.sendall(message.encode('utf-8'))  # Send '@names' directly to the server
            else:
                recipient_username, personal_message = message.split(' ', 1)
                client_socket.sendall(f"{recipient_username} {personal_message}".encode('utf-8'))
        else:
            client_socket.sendall(message.encode('utf-8'))


def main():
    host = input("Enter server IP address: ")
    port = int(input("Enter server port number: "))

    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client_socket.connect((host, port))

    username = input("Enter your username: ")
    client_socket.sendall(username.encode('utf-8'))

    welcome_message = client_socket.recv(1024).decode('utf-8')
    print(welcome_message)

    username_announcement = client_socket.recv(1024).decode('utf-8')
    print(username_announcement)

    receive_thread = threading.Thread(target=receive_messages, args=(client_socket, username))
    receive_thread.start()

    send_thread = threading.Thread(target=send_messages, args=(client_socket, username))
    send_thread.start()

    send_thread.join()
    receive_thread.join()

    client_socket.close()

if __name__ == "__main__":
    main()
