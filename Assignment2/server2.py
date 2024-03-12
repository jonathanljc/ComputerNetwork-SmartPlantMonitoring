import socket
import threading


class Server:
    should_stop = False

    def __init__(self, host="localhost", port=8888):
        self.host = host
        self.port = port
        self.server_socket: socket.socket = socket.socket(
            socket.AF_INET, socket.SOCK_STREAM
        )
        # self.server_socket.settimeout(5)
        self.client_sockets: list[socket.socket] = []
        self.client_names: dict[str] = {}
        self.threads: list[threading.Thread] = []
        self.running = False

    def start(self):
        self.server_socket.bind((self.host, self.port))
        self.server_socket.listen(5)
        self.running = True
        print(f"[*] Listening on {self.host}:{self.port}")

    def wait_for_username(self, client_socket: socket.socket):
        # Optional: Set a timeout feature for the server.
        while True:
            username = client_socket.recv(1024).decode("utf-8").strip()

            if username in self.client_names.values():
                msg = "[Username has already been used. Please enter another name.]"
                client_socket.sendall(msg.encode("utf-8"))
            else:
                return username

    def run(self):
        if not self.running:
            self.start()
        while self.running:
            client_socket, addr = self.server_socket.accept()
            print(f"[*] Accepted connection from {addr[0]}:{addr[1]}")

            username = self.wait_for_username(client_socket)

            client_socket.sendall(f"Welcome {username}!".encode("utf-8"))
            for client in self.client_sockets:
                client.sendall(f"\n[{username} joined]".encode("utf-8"))

            self.client_sockets.append(client_socket)
            self.client_names[client_socket] = username

            print(f"[{username} joined]")

            client_thread = threading.Thread(
                target=handle_client,
                args=(client_socket, self.client_sockets, self.client_names),
            )
            self.threads.append(client_thread)
            client_thread.start()
        self.server_socket.close()
        print("Server closed.")


def receive_msg(client_socket):
    while True:
        try:
            message = client_socket.recv(1024).decode("utf-8")
            if not message:
                continue
            return message
        except Exception as e:
            print(f"Error: {e}")
            return None


def handle_quit(client_socket, clients, client_names):
    exiting_username = client_names[client_socket]
    print(f"[{exiting_username} has left the chat]")
    message = "left the chat"
    for client in clients:
        client.sendall(f"[{exiting_username}]: {message}".encode("utf-8"))


def handle_names(client_socket, client_names):
    names = ", ".join(client_names.values())
    client_socket.sendall(f"[Connected users: {names}]".encode("utf-8"))
    print(f"[{client_names[client_socket]} requested user list]")


def handle_personal_message(client_socket, client_names, message):
    recipient_username, personal_message = message.split(" ", 1)
    recipient_username = recipient_username[1:]
    for client, username in client_names.items():
        if username == recipient_username:
            msg_fmt = f"[{client_names[client_socket]} (personal)]: {personal_message}"
            client.sendall(msg_fmt.encode("utf-8"))
            msg_fmt = f"[To {recipient_username}]: {personal_message}"
            client_socket.sendall(msg_fmt.encode("utf-8"))
            print(f"[{client_names[client_socket]} -> {recipient_username}]")
            return


def handle_client(client_socket, clients, client_names):
    while True:
        message = receive_msg(client_socket)
        if message is None:
            break
        stripped = message.strip()
        if stripped == "@quit":
            handle_quit(client_socket, clients, client_names)
            break
        elif stripped == "@names":
            handle_names(client_socket, client_names)
        elif message.startswith("@"):
            handle_personal_message(client_socket, client_names, message)
        else:
            sender_username = client_names[client_socket]
            print(f"[{sender_username}]: {message}")  # Server displays public message
            for client in clients:
                client.sendall(f"[{sender_username}]: {message}".encode("utf-8"))

    clients.remove(client_socket)
    client_socket.close()
    del client_names[client_socket]


def main():
    server = Server()
    server.run()


if __name__ == "__main__":
    main()
