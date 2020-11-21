import socket
import json
from tkinter import Tk     # from tkinter import Tk for Python 3.x
import tkinter as tk
from tkinter.filedialog import askopenfilename
import threading
import time
# from cloud_IT_project.encryption import rsa as RSA_PROTOCOL
# from Cryptodome.PublicKey import RSA
# from Cryptodome.Cipher import PKCS1_OAEP
# from Cryptodome.Signature import PKCS1_v1_5
# from Cryptodome.Hash import SHA512, SHA384, SHA256, SHA, MD5
# from Cryptodome import Random
# from base64 import b64encode, b64decode
# import rsa

HEADER = 64
PORT = 5050
PING_DELAY = 1
USER_ID_LENGTH = 36
FORMAT = "utf-8"
DISCONNECT_MESSAGE = "!DISCONNECT"
SERVER = "192.168.178.59"
ADDR = (SERVER, PORT)

clients = []  # Client_info and Client_Socket
connected_clients = []  # Clients and their threads
currently_selected_client = None


def start_connection(user):
    user_socket = user[1]
    user_socket.connect(ADDR)
    user_ID = user[0]["person"].get("id")
    user_name = user[0]["person"].get("name")
    id_message = bytes(f"{user_ID}", FORMAT)
    # Send messages (ID and name) to server to let it know who joined
    user_socket.send(id_message)
    send_length_and_message(user_name, user_socket)
    # Just keep waiting for messages to come in
    while True:
        time.sleep(PING_DELAY)  # Ping server for messages
        msg_length = user_socket.recv(HEADER).decode(FORMAT)
        if msg_length:
            msg_length = int(msg_length)
            msg = user_socket.recv(msg_length).decode(FORMAT)
            print()
            print(f"{user_name} has received a message: ")
            print(f"{msg}")


def end_connection(user):
    send(DISCONNECT_MESSAGE, "000000000000000000000000000000000000", user, 0)



def send(message, recipient, sender, opt):
    sender_info = sender[0]
    sender_socket = sender[1]
    option_msg = bytes(f"{opt}", FORMAT)
    sender_socket.send(option_msg)  # Tell server to expect an ID (0) or Name (1)
    recipient_msg = bytes(f"{recipient}", FORMAT)
    # Send server the name or ID depending on opt
    if opt == 0:
        sender_socket.send(recipient_msg)
    elif opt == 1:
        send_length_and_message(recipient, sender_socket)
    # Now that server knows who to send message to, send message
    send_length_and_message(message, sender_socket)


def send_length_and_message(message, sender_socket):
    bmessage = bytes(f"{message}", FORMAT)
    msg_length = len(bmessage)
    send_length = str(msg_length).encode(FORMAT)
    send_length += b' ' * (HEADER - len(send_length))
    sender_socket.send(send_length)
    sender_socket.send(bmessage)


def load_client():  # Load client from JSON
    filepath = askopenfilename()
    client_file = open(filepath)
    client_info = json.load(client_file)
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client = (client_info, client_socket)
    clients.append(client)
    return client


# Script code
running = True
while running:
    print()
    if not currently_selected_client is None:
        crnt_client_name = currently_selected_client[0]["person"].get("name")
        print(f"Current client: {crnt_client_name}")
    print("Action options: <Load> <Select> <Connect> <Send> <Disconnect>")
    user_input = input("Please type action: ")
    # Load client from JSON file
    if user_input == "Load":
        client = load_client()
        currently_selected_client = client
        client_name = client[0]["person"].get("name")
        print(f"Client {client_name} loaded & selected")
    # Select which client to operate with script
    elif user_input == "Select":
        names = []
        print("<", end="")
        for x in clients:
            name = x[0]["person"].get("name")
            print(name, end=">, <")
            names.append(name)
        print(">")
        selection = input()
        found_selection = False
        for name in names:
            for item in clients:
                if item[0]["person"].get("name") == selection:
                    currently_selected_client = item
                    found_selection = True
                    print(f"{name} selected!")
        if not found_selection:
            print("Entered name not found!")
    # Connect current selection to the server
    elif user_input == "Connect":
        thread = threading.Thread(target=start_connection, args=[currently_selected_client])
        thread.start()
        connected_clients.append((currently_selected_client, thread))
    # Send a message to other client
    elif user_input == "Send":
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
            print("Can't send message, select client first")
    elif user_input == "Disconnect":  # Disconnect from server
        end_connection(currently_selected_client)
        for x in connected_clients:
            if x[0] is currently_selected_client:
                connected_clients.remove(x)
    else:
        print("Invalid input")

# msg1 = b"Hello Tony, I am Jarvis!"
# keysize = 2048
# (public, private) = RSA_PROTOCOL.newkeys(keysize)
# encrypted = b64encode(RSA_PROTOCOL.encrypt(msg1, public))
# send("Begin")
# input()
# send("Encrypted: " + encrypted.decode('ascii'))
# print("Encrypted: " + encrypted.decode('ascii'))
# input()
# send("End")
#
# send(DISCONNECT_MESSAGE)
