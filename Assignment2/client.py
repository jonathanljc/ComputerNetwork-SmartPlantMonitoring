import socket
import threading

def receive_messages(client_socket, current_username):
    while True:
        try:
            message = client_socket.recv(1024).decode('utf-8')
            if message:
                print(message)
        except Exception as e:
            print(f"Error: {e}")
            break

def send_messages(client_socket, current_username):
    while True:
        message = input("Enter message (or type '@quit' to exit): \n")
        if message == '@quit':
            client_socket.sendall(message.encode('utf-8'))
            client_socket.close()
            break
        else:
            client_socket.sendall(message.encode('utf-8'))

def main():
    while True:  # Keep looping until a unique username is provided
        host = input("Enter server IP address: ")
        port = int(input("Enter server port number: "))

        client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client_socket.connect((host, port))

        while True:  # Keep looping until a unique username is provided
            username = input("\nEnter your name: ")
            client_socket.sendall(username.encode('utf-8'))

            welcome_message = client_socket.recv(1024).decode('utf-8')

            if welcome_message.startswith("[Username"):
                print(welcome_message)
                continue
            else:
                print(welcome_message)
                break

        send_thread = threading.Thread(target=send_messages, args=(client_socket, username))
        send_thread.start()
        receive_thread = threading.Thread(target=receive_messages, args=(client_socket, username))
        receive_thread.start()

        send_thread.join()
        receive_thread.join()

        client_socket.close()

if __name__ == "__main__":
    main()
