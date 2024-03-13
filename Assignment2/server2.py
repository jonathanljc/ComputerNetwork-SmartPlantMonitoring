import socket
import threading


class Server:
    should_stop = False

    # Server initialisation method
    # Sets up the host ip and port, prepares the sockets and threads
    def __init__(self, host="localhost", port=8888):
        self.host = host
        self.port = port
        self.server_socket: socket.socket = socket.socket(
            socket.AF_INET, socket.SOCK_STREAM
        )
        # self.server_socket.settimeout(5)
        self.client_sockets: list[socket.socket] = []
        self.client_names: dict[socket.socket, str] = {}
        self.groups: dict[str, set[str]] = {}
        self.threads: list[threading.Thread] = []
        self.running = False

    # Starts the server (starts listening for clients)
    def start(self):
        self.server_socket.bind((self.host, self.port))
        self.server_socket.listen(5)
        self.running = True
        print(f"[*] Listening on {self.host}:{self.port}")

    # Waits for client to enter username and does a check whether it already been used when entered
    def wait_for_username(self, client_socket: socket.socket):
        # Optional: Set a timeout feature for the server.
        while True:
            username = client_socket.recv(1024).decode("utf-8").strip()

            if username in self.client_names.values():
                msg = "[Username has already been used. Please enter another name.]"
                client_socket.sendall(msg.encode("utf-8"))
            else:
                return username

    # FOR TEAM: I realised this method isn't called at all
    def notify_clients(self, message):
        for client in self.client_sockets:
            client.sendall(message.encode("utf-8"))

    # Runs the server
    def run(self):
        # Calls the start() method to start the server, if it is not already running
        if not self.running:
            self.start()

        while self.running:
            # Accepts new clients attempting to connect
            try:
                client_socket, addr = self.server_socket.accept()
            except Exception as e:
                print(f"Error: {e}")
                break
            print(f"[*] Accepted connection from {addr[0]}:{addr[1]}")

            # Waits for client to enter their username
            username = self.wait_for_username(client_socket)

            client_socket.sendall(f"Welcome {username}!".encode("utf-8"))

            # Notify existing clients about the new client joining
            for client in self.client_sockets:
                client.sendall(f"\n[{username} joined]".encode("utf-8"))

            # Adds client to the list of client names
            self.client_sockets.append(client_socket)
            self.client_names[client_socket] = username

            print(f"[{username} joined]")

            # Creates and starts a thread to handle the client's actions
            client_thread = threading.Thread(
                target=handle_client,
                args=(client_socket, self.client_sockets, self.client_names, self.groups),
            )
            self.threads.append(client_thread)
            client_thread.start()

        # by the way, this code is never technically reached
        self.server_socket.close()
        print("Server closed.")

# Method to handle a client quitting the chat
# Removes name from list of users and notifies all users that this user has left
def handle_quit(client_socket, clients, client_names):
    exiting_username = client_names[client_socket]
    print(f"[{exiting_username} has left the chat]")
    message = "left the chat"
    for client in clients:
        client.sendall(f"[{exiting_username}]: {message}".encode("utf-8"))

# Method to send client the list of connected users
def handle_names(client_socket, client_names):
    names = ", ".join(client_names.values())
    client_socket.sendall(f"[Connected users: {names}]".encode("utf-8"))
    print(f"[{client_names[client_socket]} requested user list]")

# Method to take client's personal message and send to the targeted user
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

# Method for client to setup a group chat
def handle_group_setup(client_socket, client_names, groups, message):
    try:
        # Check if the format entered is correct when setting up a group
        parts = message.split()
        if len(parts) < 4:
            client_socket.sendall(
                "[Invalid format. Usage: @group set group_name user1,user2,...]".encode(
                    "utf-8"
                )
            )
            return

        _, _, group_name, users = parts
        group_name = group_name.strip()
        users_list = users.split(",")

        # Check if the group name already exists
        if group_name in groups:
            client_socket.sendall(f"[Group '{group_name}' already exists.]".encode("utf-8"))
            return

        # Check if all users in the group exist
        for username in users_list:
            if username not in client_names.values():
                client_socket.sendall(f"[User '{username}' does not exist.]".encode("utf-8"))
                return

        # Create the group and add users to it
        groups[group_name] = set(users_list)

        for username in users_list:
            for user_socket, name in client_names.items():
                if name == username:
                    print(f"Adding {username} to group {group_name}")
                    user_socket.sendall(
                        f"[You have been added to the {group_name} group]".encode(
                            "utf-8"
                        )
                    )

        # Send setup notification to the client who initiated the group setup
        client_socket.sendall(
            f"[Group '{group_name}' has been successfully created.]".encode("utf-8")
        )

    except Exception as e:
        client_socket.sendall(f"[Error setting up group: {e}]".encode("utf-8"))

# Method for client to send a message in the group chat
def handle_group_send(client_socket, client_names, groups, message):
    try:
        # Check if the format entered is correct to send a group message
        parts = message.split(maxsplit=3)
        if len(parts) < 4:
            client_socket.sendall(
                "[Invalid format. Usage: @group send group_name message]".encode(
                    "utf-8"
                )
            )
            return

        _, _, group_name, send_message = parts
        group_name = group_name.strip()

        # Check if group exists
        if group_name not in groups:
            client_socket.sendall("[Group does not exist.]".encode("utf-8"))
            return

        sender_username = client_names[client_socket]

        # Check if client is inside the group
        if sender_username not in groups[group_name]:
            client_socket.sendall("[You are not a member of this group.]".encode("utf-8"))
            return

        # Sends message to everyone in the group
        for username in groups[group_name]:
            if username != sender_username:
                user_socket = [
                    socket
                    for socket, name in client_names.items()
                    if name == username
                ][0]
                msg_fmt = f"[{sender_username} (group {group_name})]: {send_message}"
                user_socket.sendall(msg_fmt.encode("utf-8"))
    except Exception as e:
        client_socket.sendall(f"[Error sending group message: {e}]".encode("utf-8"))

# FOR TEAM: this method isn't called at all
def send_group_setup_notification(
    client_sockets, client_names, group_name, users_list
):
    for username in users_list:
        for socket, name in client_names.items():
            if name == username:
                print(f"Sending group setup notification to {name}")
                notification = f"[{username} have been added to the {group_name} group]"
                socket.sendall(notification.encode("utf-8"))

# Method for client deleting a group
def handle_group_delete(client_socket, client_names, groups, message):
    try:
        # Check if format entered is correct to delete the group
        parts = message.split(maxsplit=2)
        if len(parts) < 2:
            client_socket.sendall(
                "[Invalid format. Usage: @group delete group_name]".encode("utf-8")
            )
            return

        group_name = parts[-1].strip()  # Extract the last part as the group name

        # Check if group exists
        if group_name not in groups:
            client_socket.sendall(
                f"[Group '{group_name}' does not exist.]".encode("utf-8")
            )
            return

        # Notify all users in the group about the deletion
        for username in groups[group_name]:
            for user_socket, name in client_names.items():
                if name == username:
                    user_socket.sendall(
                        f"[Group '{group_name}' has been deleted.]".encode("utf-8")
                    )

        # Deletes the group and notifies
        del groups[group_name]
        client_socket.sendall(
            f"[Group '{group_name}' has been successfully deleted.]".encode("utf-8")
        )
    except Exception as e:
        client_socket.sendall(f"[Error deleting group: {e}]".encode("utf-8"))



# Method for client leaving a group
def handle_group_leave(client_socket, client_names, groups, message):
    try:
        # Check if the format entered is correct to leave the group
        parts = message.split(" ")
        if len(parts) < 3:
            client_socket.sendall(
                "[Invalid format. Usage: @group leave group_name]".encode("utf-8")
            )
            return

        _, _, group_name = parts
        group_name = group_name.strip()

        # Check if group exists
        if group_name not in groups:
            client_socket.sendall("[Group does not exist.]".encode("utf-8"))
            return

        # Check if user is part of this group
        sender_username = client_names[client_socket]
        if sender_username not in groups[group_name]:
            client_socket.sendall("[You are not a member of this group.]".encode("utf-8"))
            return

        # Removes user from the group
        groups[group_name].remove(sender_username)

        # Notifies clients that this user has left the group
        msg_fmt = f"[{sender_username} has left the {group_name} group.]"
        for client_socket, username in client_names.items():
            if username in groups[group_name]:
                client_socket.sendall(msg_fmt.encode("utf-8"))
        client_socket.sendall(
            f"[You have successfully left the {group_name} group.]".encode("utf-8")
        )
    except Exception as e:
        client_socket.sendall(f"[Error leaving group: {e}]".encode("utf-8"))

# Methods that handles all the client's actions
def handle_client(client_socket, clients, client_names, groups):
    while True:
        try:
            # Receives the client's message
            message = client_socket.recv(1024).decode("utf-8")
            if not message:
                continue
            stripped = message.strip()

            # If message is "@quit", calls handle_quit() to handle the client's quitting action
            if stripped == "@quit":
                handle_quit(client_socket, clients, client_names)
                break

            # If message is "@names", calls handle_names() to display names back to client
            elif stripped == "@names":
                handle_names(client_socket, client_names)

            # If message is "@group set",calls handle_group_setup() to setup the group
            elif stripped.startswith("@group set"):
                handle_group_setup(client_socket, client_names, groups, stripped)

            # If message is "@group send",calls handle_group_send() to send message to group
            elif stripped.startswith("@group send"):
                handle_group_send(client_socket, client_names, groups, stripped)
            
            # If message is "@group delete",calls handle_group_delete() to delete group
            elif stripped.startswith("@group delete"):
                handle_group_delete(client_socket, client_names, groups, stripped)
            
            # If message is "@group leave",calls handle_group_leave() to make the client leave the group
            elif stripped.startswith("@group leave"):
                handle_group_leave(client_socket, client_names, groups, stripped)
            
            # If message is "@xxxx",calls handle_personal_message() to help client send a private message to target
            elif stripped.startswith("@"):
                handle_personal_message(client_socket, client_names, message)
            else:
                # Sends a message to the main chat
                sender_username = client_names[client_socket]
                msg_fmt = f"[{sender_username}]: {message}"
                print(msg_fmt)
                for client in clients:
                    client.sendall(msg_fmt.encode("utf-8"))
        except Exception as e:
            print(f"Error: {e}")
            break

    clients.remove(client_socket)
    client_socket.close()
    del client_names[client_socket]


def main():
    # Initialises the server and runs it
    server = Server()
    server.run()


if __name__ == "__main__":
    main()
