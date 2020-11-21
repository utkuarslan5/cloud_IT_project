import socket
import json
from tkinter import Tk     # from tkinter import Tk for Python 3.x
import tkinter as tk
from tkinter.filedialog import askopenfilename
import threading
import time
from cloud_IT_project.encryption import rsa as RSA_PROTOCOL
from Cryptodome.PublicKey import RSA
from Cryptodome.Cipher import PKCS1_OAEP
from Cryptodome.Signature import PKCS1_v1_5
from Cryptodome.Hash import SHA512, SHA384, SHA256, SHA, MD5
from Cryptodome import Random
from base64 import b64encode, b64decode
import rsa

HEADER = 64
PORT = 5050
PING_DELAY = 1
USER_ID_LENGTH = 36
FORMAT = "utf-8"
DISCONNECT_MESSAGE = "!DISCONNECT"
SERVER = "192.168.178.21"
ADDR = (SERVER, PORT)
USER_ID = "5856e6cd-0da6-4573-9a04-cbb11f5e68d3"

clients = []
connected_clients = []
currently_selected_client = None


def start_connection(user_name):
    for x in clients:
        if x[0].get("name") == user_name:
            user = x
    user_socket = user[1]
    user_socket.connect(ADDR)
    user_ID = currently_selected_client[0].get("id")
    message = bytes(f"{user_ID}", FORMAT)
    user_socket.send(message)  # Send message to server to let know who joined
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


def end_connection(user_name):
    send(DISCONNECT_MESSAGE, "000000000000000000000000000000000000", user_name)



def send(message, recipient_ID, sender):
    for x in connected_clients:
        if x[0][0].get("name") == sender:
            sender_socket = x[0][1]
    recipient_msg = bytes(f"{recipient_ID}", FORMAT)
    sender_socket.send(recipient_msg)
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
        crnt_client_name = currently_selected_client[0].get("name")
        print(f"Current client: {crnt_client_name}")
    print("Action options: <Load> <Select> <Connect> <Send> <Disconnect>")
    user_input = input("Please type action: ")
    if user_input == "Load":  # Load client from JSON file
        client = load_client()
        currently_selected_client = client
        client_name = client[0].get("name")
        print(f"Client {client_name} loaded & selected")
    elif user_input == "Select":  # Select which client to operate with script
        names = []
        print("<",end="")
        for x in clients:
            name = x[0].get("name")
            print(name, end=">, <")
            names.append(name)
        print(">")
        selection = input()
        found_selection = False
        for name in names:
            for item in clients:
                if item[0].get("name") == selection:
                    currently_selected_client = item
                    found_selection = True
                    print(f"{name} selected!")
        if not found_selection:
            print("Entered name not found!")
    elif user_input == "Connect":  # Connect current selection to the server
        thread = threading.Thread(target=start_connection, args=[crnt_client_name])
        thread.start()
        connected_clients.append((currently_selected_client, thread))
    elif user_input == "Send":  # Send a message to other client
        if not currently_selected_client is None:
            recipient = input("Send to: ")
            msg = input("Message: ")
            send(msg, recipient, crnt_client_name)
        else:
            print("Can't send message, select client first")
    elif user_input == "Disconnect":  # Disconnect from server
        end_connection(crnt_client_name)
        for x in connected_clients:
            if x[0] is currently_selected_client:
                connected_clients.remove(x)
    else:
        print("Invalid input")

msg1 = b"Hello Tony, I am Jarvis!"
keysize = 2048
(public, private) = RSA_PROTOCOL.newkeys(keysize)
encrypted = b64encode(RSA_PROTOCOL.encrypt(msg1, public))
send("Begin")
input()
send("Encrypted: " + encrypted.decode('ascii'))
print("Encrypted: " + encrypted.decode('ascii'))
#send(pkg)
input()
send("End")

send(DISCONNECT_MESSAGE)
