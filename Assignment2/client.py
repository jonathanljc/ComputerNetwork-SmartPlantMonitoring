import socket
import threading

def receive_messages(client_socket, current_username):
    previous_message = None  # Initialize previous message variable
    while True:
        try:
            message = client_socket.recv(1024).decode('utf-8')
            if message != previous_message:  # Check if message is different from the previous one
                if message.startswith("[") and message.endswith(" joined]"):
                    print(message)
                elif message.startswith("[") and message.endswith(" group]"):
                    print(message.replace("You", current_username))
                elif ':' in message:
                    sender, message_body = message.split(':', 1)
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
                previous_message = message  # Update previous message variable
        except Exception as e:
            print(f"Error: {e}")
            break


def send_messages(client_socket, current_username):
    while True:
        message = input("Enter message (or type '@quit' to exit): \n")
        if message == '@quit':
            client_socket.sendall(message.encode('utf-8'))
            client_socket.close()  # Close the client socket
            break
        elif message.startswith('@group set'):
            parts = message.split()
            if len(parts) < 4:
                print("Invalid format. Usage: @group set group_name user1,user2,user3,...")
                continue
            else:
                print("Sending group setup command:", message)
                client_socket.sendall(message.encode('utf-8'))
        elif message.startswith('@'):
            if message.strip() == "@names":
                client_socket.sendall(message.encode('utf-8'))  # Send '@names' directly to the server
            else:
                recipient_username, personal_message = message.split(' ', 1)
                client_socket.sendall(f"{recipient_username} {personal_message}".encode('utf-8'))
        elif message.startswith('@group send'):
            parts = message.split(maxsplit=2)
            if len(parts) < 3:
                print("Invalid format. Usage: @group send group_name message")
                continue
            else:
                _, group_name, send_message = parts
                group_name = group_name.strip()
                message_to_send = f"@group send {group_name} {send_message}"
                print("Sending group message:", message_to_send)
                client_socket.sendall(message_to_send.encode('utf-8'))
        else:
            client_socket.sendall(message.encode('utf-8'))

def main():
    host = input("Enter server IP address: ")
    port = int(input("Enter server port number: "))

    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client_socket.connect((host, port))

    while True:
        username = input("\nEnter your name: ")
        client_socket.sendall(username.encode('utf-8'))

        welcome_message = client_socket.recv(1024).decode('utf-8')

        if welcome_message.startswith("[Username"):
            print(welcome_message)
        else:
            print(welcome_message)

            send_thread = threading.Thread(target=send_messages, args=(client_socket, username))
            send_thread.start()
            receive_thread = threading.Thread(target=receive_messages, args=(client_socket, username))
            receive_thread.start()

            send_thread.join()
            receive_thread.join()

            client_socket.close()
            break

if __name__ == "__main__":
    main()
