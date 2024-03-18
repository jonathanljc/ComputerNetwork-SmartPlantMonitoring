import socket
import threading
import re


class Server:
    should_stop = False

    # Initialize server settings
    def __init__(self, host="localhost", port=8888):
        self.host = host
        self.port = port
        self.server_socket: socket.socket = socket.socket(
            socket.AF_INET, socket.SOCK_STREAM
        )
        self.client_sockets: list[socket.socket] = []
        self.client_names: dict[socket.socket, str] = {}
        self.groups: dict[str, set[str]] = {}
        self.owner_dict: dict[str, str] = {}  # New dictionary to store group owners
        self.threads: list[threading.Thread] = []
        self.running = False

    # Start the server
    def start(self):
        self.server_socket.bind((self.host, self.port))
        self.server_socket.listen(5)
        self.running = True
        print(f"[*] Listening on {self.host}:{self.port}")

    # Wait for the client to provide a unique username
    def wait_for_username(self, client_socket: socket.socket):
        while True:
            username = client_socket.recv(1024).decode("utf-8").strip()
            if username in self.client_names.values():
                msg = "[Username has already been used. Please enter another name.]”"
                client_socket.sendall(msg.encode("utf-8"))
            else:
                return username
    # Run the server
    def run(self):
        if not self.running:
            self.start()

        while self.running:
            try:
                client_socket, addr = self.server_socket.accept()
            except Exception as e:
                print(f"Error: {e}")
                break
            print(f"[*] Accepted connection from {addr[0]}:{addr[1]}")

            username = self.wait_for_username(client_socket)
            client_socket.sendall(f"Welcome {username}!".encode("utf-8"))

            for client in self.client_sockets:
                client.sendall(f"\n[{username} joined]".encode("utf-8"))

            self.client_sockets.append(client_socket)
            self.client_names[client_socket] = username

            print(f"[{username} joined]")

            # Create a new thread to handle the client
            client_thread = threading.Thread(
                target=handle_client,
                args=(
                    client_socket,
                    self.client_sockets,
                    self.client_names,
                    self.groups,
                    self.owner_dict,  
                ),
            )
            self.threads.append(client_thread)
            client_thread.start()

        self.server_socket.close()
        print("Server closed.")

# Function to handle individual client connections
def handle_client(client_socket, clients, client_names, groups, owner_dict):
    while True:
        try:
            message = client_socket.recv(1024).decode("utf-8")
            if not message:
                continue
            stripped = message.strip()

            # Handle different commands
            if stripped == "@quit":
                handle_quit(client_socket, clients, client_names)
                break
            elif stripped == "@names":
                handle_names(client_socket, client_names)
            elif stripped.startswith("@group set"):
                handle_group_setup(client_socket, client_names, groups, owner_dict, stripped)
            elif stripped.startswith("@group send"):
                handle_group_send(client_socket, client_names, groups, stripped)
            elif stripped.startswith("@group delete"):
                handle_group_delete(client_socket, client_names, groups, stripped)
            elif stripped.startswith("@group leave"):
                handle_group_leave(client_socket, client_names, groups, owner_dict, message)
            elif stripped == "@grouplist":
                handle_group_list(client_socket, client_names, groups, owner_dict, message)
            elif stripped.startswith("@kick"):
                handle_group_kick(client_socket, client_names, groups, owner_dict, stripped)
            elif stripped.startswith("@add"):
                handle_group_add(client_socket, client_names, groups, owner_dict, stripped)
            elif stripped.startswith("@who"):
                handle_group_members(client_socket, client_names, groups, stripped)
            elif stripped == "@help":
                handle_help(client_socket)
            elif stripped.startswith("@"):
                if stripped == "@":
                    client_socket.sendall("[Please provide a valid command. Type @help for available commands.]".encode("utf-8"))
                else:
                    handle_personal_message(client_socket, client_names, message)
            else:
                sender_username = client_names[client_socket]
                msg_fmt = f"[{sender_username}:] {message}"
                print(msg_fmt)
                # Send message to all clients except the sender
                for client in clients:
                    if client != client_socket:
                        client.sendall(msg_fmt.encode("utf-8"))
        except Exception as e:
            print(f"Error: {e}")
            break

    # Remove the client from the active client list
    clients.remove(client_socket)
    client_socket.close()
    del client_names[client_socket]



# Handles the case when a client exits the chat. Notifies other clients about the exit.
def handle_quit(client_socket, clients, client_names):
    exiting_username = client_names[client_socket]
    print(f"[{exiting_username} has left the chat]")
    message = "exited"
    for client in clients:
        client.sendall(f"{exiting_username} {message}".encode("utf-8"))

# Responds to a client's request for the list of connected users.
def handle_names(client_socket, client_names):
    try:
        names = ", ".join(client_names.values())
        client_socket.sendall(f"[Connected users: {names}]".encode("utf-8"))
        print(f"[{client_names[client_socket]} requested user list]")
    except Exception as e:
        print(f"Error handling names: {e}")
        client_socket.sendall("[Error retrieving user list.]".encode("utf-8"))

# Manages sending personal messages between clients.
def handle_personal_message(client_socket, client_names, message):
    try:
        recipient_username, personal_message = message.split(" ", 1)
        recipient_username = recipient_username[1:]

        recipient_socket = None
        for socket, username in client_names.items():
            if username == recipient_username:
                recipient_socket = socket
                break

        if recipient_socket:
            msg_fmt_recipient = f"[Personal Message from {client_names[client_socket]}]: {personal_message}"
            recipient_socket.sendall(msg_fmt_recipient.encode("utf-8"))
            print(f"[{client_names[client_socket]} -> {recipient_username}]")
        else:
            client_socket.sendall(f"[User '{recipient_username}' not found. Type @help for available commands.]".encode("utf-8"))

    except ValueError:
        client_socket.sendall("[Please provide a valid command. Type @help for available commands.]".encode("utf-8"))




# Sets up a new group with specified users. Notifies users about being added to the group.
def handle_group_setup(client_socket, client_names, groups, owner_dict, message):
    try:
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

        # Regular expression pattern to match alphanumeric characters
        alphanumeric_pattern = re.compile("^[a-zA-Z0-9_]+$")

        # Check if the group name contains only alphanumeric characters
        if not alphanumeric_pattern.match(group_name):
            client_socket.sendall(
                "[Group name can only contain alphanumeric characters.]".encode("utf-8")
            )
            return

        if group_name in groups:
            client_socket.sendall(
                f"[Group '{group_name}' already exists.]".encode("utf-8")
            )
            return

        # Check if the client creating the group is in the list of users
        client_username = client_names[client_socket]
        if client_username not in users_list:
            client_socket.sendall(
                f"[You must be a part of the group to create it.]".encode("utf-8")
            )
            return

        for username in users_list:
            if username not in client_names.values():
                client_socket.sendall(
                    f"[User '{username}' does not exist.]".encode("utf-8")
                )
                return

        groups[group_name] = set(users_list)
        owner_dict[group_name] = client_username  # Store owner information

        for username in users_list:
            for user_socket, name in client_names.items():
                if name == username:
                    print(f"Adding {username} to group {group_name}")
                    user_socket.sendall(
                        f"[[You are enrolled in the {group_name} group]".encode(
                            "utf-8"
                        )
                    )

        client_socket.sendall(
            f"[Group '{group_name}' has been successfully created.]".encode("utf-8")
        )

    except Exception as e:
        client_socket.sendall(f"[Error setting up group: {e}]".encode("utf-8"))

# Adds a user to an existing group, with permission checks.
def handle_group_add(client_socket, client_names, groups, owner_dict, message):
    try:
        parts = message.split(maxsplit=2)
        if len(parts) < 3:
            client_socket.sendall(
                "[Invalid format. Usage: @add group_name user_to_add]".encode("utf-8")
            )
            return

        _, group_name, user_to_add = parts
        group_name = group_name.strip()

        if group_name not in groups:
            client_socket.sendall("[Group does not exist.]".encode("utf-8"))
            return

        owner = owner_dict.get(group_name)
        if owner != client_names[client_socket]:
            client_socket.sendall("[You are not the owner of this group.]".encode("utf-8"))
            return

        if user_to_add in groups[group_name]:
            client_socket.sendall(f"[{user_to_add} is already a member of {group_name}]".encode("utf-8"))
            return

        if user_to_add not in client_names.values():
            client_socket.sendall(f"[User '{user_to_add}' does not exist.]".encode("utf-8"))
            return

        groups[group_name].add(user_to_add)

        # Notify the added user
        for user_socket, username in client_names.items():
            if username == user_to_add:
                user_socket.sendall(f"[You have been added to the {group_name} group]".encode("utf-8"))

        client_socket.sendall(
            f"[{user_to_add} has been added to the {group_name} group.]".encode("utf-8")
        )

    except Exception as e:
        client_socket.sendall(f"[Error adding member: {e}]".encode("utf-8"))

# Retrieves and sends the list of members of a group to the client.
def handle_group_members(client_socket, client_names, groups, message):
    try:
        parts = message.split()
        if len(parts) != 2:
            client_socket.sendall(
                "[Invalid format. Usage: @who group_name]".encode("utf-8")
            )
            return

        _, group_name = parts
        group_name = group_name.strip()

        if group_name not in groups:
            client_socket.sendall(
                f"[Group '{group_name}' does not exist.]".encode("utf-8")
            )
            return

        # Check if the client is a member of the specified group
        sender_username = client_names[client_socket]
        if sender_username not in groups[group_name]:
            client_socket.sendall(
                f"[You are not a member of the '{group_name}' group.]".encode("utf-8")
            )
            return

        members = ", ".join(groups[group_name])
        client_socket.sendall(
            f"[Members of '{group_name}' group: {members}]".encode("utf-8")
        )

    except Exception as e:
        client_socket.sendall(f"[Error getting group members: {e}]".encode("utf-8"))

# Sends a message to a specified group, with appropriate permissions and error handling.
def handle_group_send(client_socket, client_names, groups, message):
    try:
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

        if group_name not in groups:
            client_socket.sendall("[Group does not exist.]".encode("utf-8"))
            return

        sender_username = client_names[client_socket]

        if sender_username not in groups[group_name]:
            client_socket.sendall(
                "[You are not a member of this group.]".encode("utf-8")
            )
            return

        for username in groups[group_name]:
            if username != sender_username:
                user_socket = [
                    socket for socket, name in client_names.items() if name == username
                ][0]
                msg_fmt = f"[{sender_username} (group {group_name})]: {send_message}"
                user_socket.sendall(msg_fmt.encode("utf-8"))
    except Exception as e:
        client_socket.sendall(f"[Error sending group message: {e}]".encode("utf-8"))

#  Lists the groups the client is a member of, including those they own.
def handle_group_list(client_socket, client_names, groups, owner_dict, message):
    try:
        parts = message.split(maxsplit=1)
        if len(parts) < 1:
            client_socket.sendall(
                "[Invalid format. Usage: @grouplist]".encode("utf-8")
            )
            return

        client_username = client_names[client_socket]
        user_groups = [group for group, members in groups.items() if client_username in members]
        owned_groups = [group for group, owner in owner_dict.items() if owner == client_username]

        if not user_groups:
            client_socket.sendall(
                "[You are not a member of any group.]".encode("utf-8")
            )
            return

        groups_list = ", ".join(user_groups)
        response = f"[You are in the following groups: {groups_list}]\n"

        if owned_groups:
            owned_group_names = ", ".join(owned_groups)
            response += f"[You are the owner of the following groups: {owned_group_names}]"

        client_socket.sendall(response.encode("utf-8"))

    except Exception as e:
        client_socket.sendall(f"[Error showing groups: {e}]".encode("utf-8"))


# Deletes a specified group, notifying its members.
def handle_group_delete(client_socket, client_names, groups, message):
    try:
        parts = message.split(maxsplit=2)
        if len(parts) < 2:
            client_socket.sendall(
                "[Invalid format. Usage: @group delete group_name]".encode("utf-8")
            )
            return

        group_name = parts[-1].strip()

        if group_name not in groups:
            client_socket.sendall(
                f"[Group '{group_name}' does not exist.]".encode("utf-8")
            )
            return

        for username in groups[group_name]:
            for user_socket, name in client_names.items():
                if name == username:
                    user_socket.sendall(
                        f"[Group '{group_name}' has been deleted.]".encode("utf-8")
                    )

        del groups[group_name]
        client_socket.sendall(
            f"[Group '{group_name}' has been successfully deleted.]".encode("utf-8")
        )
    except Exception as e:
        client_socket.sendall(f"[Error deleting group: {e}]".encode("utf-8"))

# Manages a client leaving a group, with consideration for ownership and notifying members.
def handle_group_leave(client_socket, client_names, groups, owner_dict, message):
    try:
        parts = message.split(" ")
        if len(parts) < 3:
            client_socket.sendall(
                "[Invalid format. Usage: @group leave group_name]".encode("utf-8")
            )
            return

        _, _, group_name = parts
        group_name = group_name.strip()

        if group_name not in groups:
            client_socket.sendall("[Group does not exist.]".encode("utf-8"))
            return

        sender_username = client_names[client_socket]
        if sender_username not in groups[group_name]:
            client_socket.sendall(
                "[You are not a member of this group.]".encode("utf-8")
            )
            return

        groups[group_name].remove(sender_username)

        if sender_username == owner_dict.get(group_name):  # Check if leaving member is the owner
            # Select a new owner from the remaining members
            new_owner = next(iter(groups[group_name])) if groups[group_name] else None
            owner_dict[group_name] = new_owner

            if new_owner:
                msg_fmt = f"[{sender_username} has left the {group_name} group.]"
                msg_fmt_new_owner = f"[You have been assigned as the new owner of {group_name}]"
                for user_socket, username in client_names.items():
                    if username == new_owner:
                        user_socket.sendall(msg_fmt_new_owner.encode("utf-8"))
        
       # msg_fmt = f"[{sender_username} has left the {group_name} group.]"
        for client_socket, username in client_names.items():
            if username in groups[group_name]:
                client_socket.sendall(msg_fmt.encode("utf-8"))
        client_socket.sendall(
            f"[You have successfully left the {group_name} group.]".encode("utf-8")
        )
    except Exception as e:
        client_socket.sendall(f"[Error leaving group: {e}]".encode("utf-8"))


# Allows the owner to kick a user out of a group, notifying the user and other members.
def handle_group_kick(client_socket, client_names, groups, owner_dict, message):
    try:
        parts = message.split(maxsplit=2)
        if len(parts) < 3:
            client_socket.sendall(
                "[Invalid format. Usage: @kick group_name user_to_kick]".encode("utf-8")
            )
            return

        _, group_name, user_to_kick = parts
        group_name = group_name.strip()

        if group_name not in groups:
            client_socket.sendall("[Group does not exist.]".encode("utf-8"))
            return

        owner = owner_dict.get(group_name)
        if owner == client_names[client_socket]:
            if user_to_kick in groups[group_name]:
                if user_to_kick == owner:  # Prevent the owner from kicking themselves out
                    client_socket.sendall("[You cannot kick yourself out of the group.]".encode("utf-8"))
                else:
                    groups[group_name].remove(user_to_kick)
                    msg_fmt_kicked_user = f"[You have been kicked from {group_name} by {client_names[client_socket]}]"

                    # Find the socket of the user to kick and send them a notification
                    for user_socket, username in client_names.items():
                        if username == user_to_kick:
                            user_socket.sendall(msg_fmt_kicked_user.encode("utf-8"))

                    # Notify other users in the group
                    msg_fmt_other_users = f"[{user_to_kick} has been kicked from {group_name}]"
                    for client_socket, username in client_names.items():
                        if username in groups[group_name] and client_socket != client_names[client_socket]:
                            client_socket.sendall(msg_fmt_other_users.encode("utf-8"))
            else:
                client_socket.sendall(f"[{user_to_kick} is not a member of {group_name}]".encode("utf-8"))
        else:
            client_socket.sendall("[You are not the owner of this group.]".encode("utf-8"))

    except Exception as e:
        client_socket.sendall(f"[Error kicking member: {e}]".encode("utf-8"))

# Provides a help message with available commands and their descriptions.
def handle_help(client_socket):
    help_message = """
    General commands:
    @quit: Exit the chat.
    @names: List all connected users.
    @[username] <message>: Send a personal message to a user.
    @help: Display this help message.

    Group-related commands:
    @group set <group_name> <user1,user2,...>: Create a new group.
    @group send <group_name> <message>: Send a message to a group.
    @group delete <group_name>: Delete a group (only available for group owners).
    @group leave <group_name>: Leave a group.
    @grouplist: List the groups you are a member of.
    @who <group_name>: See the members of a specific group.

    Group management commands (only available for group owners):
    @kick <group_name> <user_to_kick>: Kick a user out of a group.
    @add <group_name> <user_to_add>: Add a user to a group.

   
    """
    client_socket.sendall(help_message.encode("utf-8"))







def main():
    server = Server()
    server.run()


if __name__ == "__main__":
    main()
