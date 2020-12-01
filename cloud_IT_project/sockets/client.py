import socket
import json
from tkinter.filedialog import askopenfilename
import threading
from cloud_IT_project.encryption.rsa import exportKey, importKey, newkeys, decrypt, encrypt

HEADER = 64
PORT = 5050
PING_DELAY = 10
USER_ID_LENGTH = 36
FORMAT = "utf-8"
DISCONNECT_MESSAGE = "!DISCONNECT"
SERVER = "192.168.178.21"
ADDR = (SERVER, PORT)
KEYSIZE = 1024

clients = []  # Client_info
organizations = []  # Org_info and Org_Socket
connected_clients = []  # Clients and their threads
currently_selected_client = None


def start_connection(user):
    user_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    user["socket"] = user_socket
    user_socket.connect(ADDR)
    if user.get("type") == "User":
        option_msg = bytes(f"{0}", FORMAT)
        user_socket.send(option_msg)  # Tell server to expect a user
        user_ID = user["person"].get("id")
        user_name = user["person"].get("name")
        user_public_key = exportKey(user["person"]["keys"].get("public"))
        id_message = bytes(f"{user_ID}", FORMAT)
        # Send messages (ID and name) to server to let it know who joined
        user_socket.send(id_message)
        send_str_length_and_message(user_name, user_socket)
        send_byte_length_and_message(user_public_key, user_socket)
        # Just keep waiting for messages to come in
        while user["connected"]:
            msg_length = user_socket.recv(HEADER).decode(FORMAT)
            sending = user["send_info"]["sending"]
            if msg_length:
                if not sending:
                    sender_length = int(msg_length)
                    sender = user_socket.recv(sender_length)
                    sender = sender.decode(FORMAT)
                    msg_length = user_socket.recv(HEADER).decode(FORMAT)
                    msg_length = int(msg_length)
                    msg = user_socket.recv(msg_length)
                    decrypted_msg = decrypt(msg, user["person"]["keys"].get("private"))
                    decrypted_msg = decrypted_msg.decode(FORMAT)
                    print()
                    print(f"{user_name} has received a message: ")
                    print(f"{sender} {decrypted_msg}")
                elif sending:
                    key_length = int(msg_length)
                    key = user_socket.recv(key_length)
                    user["send_info"]["pub_key"] = importKey(key)
    elif user.get("type") == "Organization":
        option_msg = bytes(f"{1}", FORMAT)
        user_socket.send(option_msg)  # Tell server to expect an organization
        send_str_length_and_message(user.get("name"), user_socket)
        number_of_employees = len(user["employees"])  # Tell server how many employees the organization has
        num_employees_msg = str(number_of_employees).encode(FORMAT)
        num_employees_msg += b' ' * (HEADER - len(num_employees_msg))
        user_socket.send(num_employees_msg)
        for employee in user.get("employees"):
            send_str_length_and_message(employee.get("id"), user_socket)
            send_str_length_and_message(employee.get("role"), user_socket)


    user["socket"] = None


def end_connection(user):
    user["socket"].send(bytes(f"2", FORMAT))
    user["connected"] = False


def send(message, recipient, sender, opt):
    sender["send_info"]["sending"] = True
    sender_socket = sender["socket"]
    option_msg = bytes(f"{opt}", FORMAT)
    sender_socket.send(option_msg)  # Tell server to expect an ID (0) or Name (1)
    recipient_msg = bytes(f"{recipient}", FORMAT)
    # Send server the name or ID depending on opt
    if opt == 0:
        sender_socket.send(recipient_msg)
    elif opt == 1:
        send_str_length_and_message(recipient, sender_socket)
    key_received = False
    while not key_received:
        if sender["send_info"]["pub_key"]:
            key_received = True
    key = sender["send_info"]["pub_key"]
    # Message encryption
    bmessage = bytes(message, FORMAT)
    encrypted_msg = encrypt(bmessage, key)
    # Now that server knows who to send message to, send message
    send_byte_length_and_message(encrypted_msg, sender_socket)
    sender["send_info"]["sending"] = False
    print("Message Sent!")


def send_str_length_and_message(message, sender_socket):
    bmessage = bytes(f"{message}", FORMAT)
    msg_length = len(bmessage)
    send_length = str(msg_length).encode(FORMAT)
    send_length += b' ' * (HEADER - len(send_length))
    sender_socket.send(send_length)
    sender_socket.send(bmessage)


def send_byte_length_and_message(message, sender_socket):
    msg_length = len(message)
    send_length = str(msg_length).encode(FORMAT)
    send_length += b' ' * (HEADER - len(send_length))
    sender_socket.send(send_length)
    sender_socket.send(message)


def load_client(load_option):  # Load client from JSON
    if load_option == "User":
        filepath = askopenfilename()
        client_file = open(filepath)
        client_info = json.load(client_file)
        pub, pri = newkeys(KEYSIZE)
        client_info["person"]["keys"]["private"] = pri
        client_info["person"]["keys"]["public"] = pub
        client_info["send_info"] = {"sending": False, "pub_key": None}
        client_info["type"] = "User"
        client_info["connected"] = False
        client = client_info
        clients.append(client)
        client_name = client_info["person"]["name"]
        print(f"{client_name} loaded & selected")
        return client
    elif load_option == "Organizations":
        filepath = askopenfilename()
        org_file = open(filepath)
        org_info = json.load(org_file)
        for org in org_info["organizations"]:
            org["type"] = "Organization"
            org["connected"] = False
            organizations.append(org)
            org_name = org.get("name")
            print(f"Loaded {org_name}")
        return None


# Script code
running = True
while running:
    print()
    if not currently_selected_client is None:
        menu_type = currently_selected_client["type"]
        connected = currently_selected_client["connected"]
        if menu_type == "User":
            crnt_client_name = currently_selected_client["person"].get("name")
            print(f"Current user: {crnt_client_name}")
            if connected:
                print("Action options: <Load> <Select> <Send> <Disconnect>")
            elif not connected:
                print("Action options: <Load> <Select> <Connect>")
        elif menu_type == "Organization":
            crnt_client_name = currently_selected_client["name"]
            print(f"Current user: {crnt_client_name}")
            if connected:
                print("Action options: <Load> <Select>")
            elif not connected:
                print("Action options: <Load> <Select> <Connect>")
    else:
        menu_type = "None"
        connected = False
        print("Action options: <Load> <Select>")
    user_input = input("Please type action: ")
    # Load client from JSON file
    if user_input == "Load" and (menu_type == "None" or menu_type == "User" or menu_type == "Organization"):
        print("Load options: <User> <Organizations>")
        load_type = input("Please type option: ")
        if load_type == "User" or load_type == "Organizations":
            client = load_client(load_type)
            currently_selected_client = client
        else:
            print("Invalid option.")
    # Select which client to operate with script
    elif user_input == "Select" and (menu_type == "None" or menu_type == "User" or menu_type == "Organization"):
        names = []
        print("Selection options: ")
        print("<", end="")
        for x in clients:
            name = x["person"].get("name")
            print(name, end=">, <")
            names.append(name)
        for x in organizations:
            name = x.get("name")
            print(name, end=">, <")
            names.append(name)
        print(">")
        print("Connected users: ")
        print("<", end="")
        for x in connected_clients:
            if x[0]["type"] == "User":
                name = x[0]["person"].get("name")
            elif x[0]["type"] == "Organization":
                name = x[0]["name"]
            print(name, end=">, <")
            names.append(name)
        print(">")
        selection = input("Select user: ")
        found_selection = False
        for item in clients:
            if item["person"].get("name") == selection:
                currently_selected_client = item
                found_selection = True
                name = currently_selected_client["person"]["name"]
                print(f"{name} selected!")
                break
        for item in organizations:
            if item.get("name") == selection:
                currently_selected_client = item
                found_selection = True
                name = currently_selected_client["name"]
                print(f"{name} selected!")
                break
        else:
            print("Entered name not found!")
    # Connect current selection to the server
    elif user_input == "Connect" and (menu_type == "User" or menu_type == "Organization") and not connected:
        thread = threading.Thread(target=start_connection, args=[currently_selected_client])
        thread.start()
        connected_clients.append((currently_selected_client, thread))
        currently_selected_client["connected"] = True
        print(f"{crnt_client_name} has connected!")
    # Send a message to other client
    elif user_input == "Send" and (menu_type == "User") and connected:
        if not currently_selected_client is None:
            option = input("Send using <ID> or <Name>?: ")
            if option == "ID":
                option = 0
            elif option == "Name":
                option = 1
            else:
                option = -1
                print("Not valid option")
            if option != -1:
                recipient_input = input("Send to: ")
                msg_input = input("Message: ")
                send(msg_input, recipient_input, currently_selected_client, option)
        else:
            print("Can't send message, select user first")
    # Disconnect from server
    elif user_input == "Disconnect" and (menu_type == "User") and connected:
        end_connection(currently_selected_client)
        for x in connected_clients:
            if x[0] is currently_selected_client:
                connected_clients.remove(x)
        currently_selected_client = None
        print(f"{crnt_client_name} has disconnected!")
    else:
        print("Invalid input")

