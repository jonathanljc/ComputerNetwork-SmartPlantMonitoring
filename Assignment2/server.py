import socket
import threading

def handle_client(client_socket, clients, client_names):
    while True:
        try:
            message = client_socket.recv(1024).decode('utf-8')
            if message:
                if message.strip() == "@quit":
                    exiting_username = client_names[client_socket]
                    print(f"[{exiting_username} has left the chat]")  
                    break
                elif message.strip() == "@names":
                    names = ', '.join(client_names.values())
                    client_socket.sendall(f"[Connected users: {names}]".encode('utf-8'))
                    print(f"[{client_names[client_socket]} requested user list]")
                elif message.startswith("@"):
                    recipient_username, personal_message = message.split(" ", 1)
                    recipient_username = recipient_username[1:]
                    for client, username in client_names.items():
                        if username == recipient_username:
                            client.sendall(f"[{client_names[client_socket]} (personal)]: {personal_message}".encode('utf-8'))
                            client_socket.sendall(f"[To {recipient_username}]: {personal_message}".encode('utf-8'))
                            print(f"[{client_names[client_socket]} -> {recipient_username}]")
                            break
                else:
                    sender_username = client_names[client_socket]
                    print(f"[{sender_username}]: {message}")  # Server displays public message
                    for client in clients:
                        client.sendall(f"[{sender_username}]: {message}".encode('utf-8'))
        except Exception as e:
            print(f"Error: {e}")
            break

    clients.remove(client_socket)
    client_socket.close()
    del client_names[client_socket]

def announce_new_user(clients, client_names, new_username):
    for client in clients:
        if client_names[client] != new_username:
            client.sendall(f"\n[{new_username} joined]".encode('utf-8'))



def main():
    host = 'localhost'
    port = 8888

    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.bind((host, port))
    server_socket.listen(5)

    print(f"[*] Listening on {host}:{port}")

    clients = []
    client_names = {}

    while True:
        client_socket, addr = server_socket.accept()
        print(f"[*] Accepted connection from {addr[0]}:{addr[1]}")
        
        while True:
            #client_socket.sendall("Enter your username: ".encode('utf-8'))
            username = client_socket.recv(1024).decode('utf-8').strip()

            if username in client_names.values():
                client_socket.sendall("[Username has already been used. Please enter another name.]".encode('utf-8'))
            else:
                client_socket.sendall(f"Welcome {username}!".encode('utf-8'))
                break

        clients.append(client_socket)
        client_names[client_socket] = username
        
        announce_new_user(clients, client_names, username)


        print(f"[{username} joined]")

        client_thread = threading.Thread(target=handle_client, args=(client_socket, clients, client_names))
        client_thread.start()

    server_socket.close()

if __name__ == "__main__":
    main()
