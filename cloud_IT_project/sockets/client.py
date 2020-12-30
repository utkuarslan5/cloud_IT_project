import socket
import json
from random import randint
from tkinter.filedialog import askopenfilename
import threading
from cloud_IT_project.encryption.rsa import exportKey, importKey, newkeys, decrypt, encrypt
import os

HEADER = 64
PORT = 5050
PING_DELAY = 10
FORMAT = "utf-8"
SERVER = "192.168.1.101"  # When you run the server script, and IP will appear. Paste that in here.
ADDR = (SERVER, PORT)
KEYSIZE = 1024  # RSA key length
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


clients = []  # Client_info
organizations = []  # Org_info and Org_Socket
connected_clients = []  # Clients and their threads


def start_connection(user):
    """ Starts connection to the server

    Sets up a socket for connection session.
    Handles [User] type clients and [Organization] type clients
    Steps:
    1. Sends message to let server know if client is [User] (0) or [Organization] (1)
    2. Sends server necessary data (i.e. name, id, employees, etc.)
    3. [User] ONLY - Waits for messages from server.
                     IF client is expecting another [User]'s public key,
                     THEN sending value is True. Script will receive and save key
                     ELSE Script will receive user messages. Receives sender name and message, decrypts message.
    #TODO Organizations send info but don't stay connected. That functionality needs to be added
    #TODO Visualization of this thread. Messages get printed now but need a screen (PyQt5)
    :param user: A dictionary containing all info about the user of this thread
    :return: None
    """
    user_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    user["socket"] = user_socket
    user_socket.connect(ADDR)
    if user.get("type") == "User":
        option_msg = bytes(f"{0}", FORMAT)
        user_socket.send(option_msg)
        user_ID = user["person"].get("id")
        user_name = user["person"].get("name")
        user_public_key = user["person"]["keys"].get("public")
        if isinstance(user_public_key, str):
            user_public_key = bytes(user_public_key, FORMAT)
        id_message = bytes(f"{user_ID}", FORMAT)
        send_str_length_and_message(id_message, user_socket)
        send_str_length_and_message(user_name, user_socket)
        send_byte_length_and_message(user_public_key, user_socket)
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
                    priv_key = importKey(user["person"]["keys"].get("private"))
                    decrypted_msg = decrypt(msg, priv_key)
                    decrypted_msg = decrypted_msg.decode(FORMAT)
                    print("\n")
                    print("//////////////////////////////////////////////////////////////////////////////////////")
                    print(f"{user_name} has received a message: ")
                    print(f"[{sender}] {decrypted_msg}")
                    print("//////////////////////////////////////////////////////////////////////////////////////")
                elif sending:
                    key_length = int(msg_length)
                    key = user_socket.recv(key_length)
                    user["send_info"]["pub_key"] = importKey(key)
    elif user.get("type") == "Organization":
        option_msg = bytes(f"{1}", FORMAT)
        user_socket.send(option_msg)
        org_ID = user.get("id")
        org_public_key = user["keys"].get("public")
        if isinstance(org_public_key, str):
            org_public_key = bytes(org_public_key, FORMAT)
        id_message = bytes(f"{org_ID}", FORMAT)

        send_str_length_and_message(user.get("name"), user_socket)
        send_str_length_and_message(user.get("org_type"), user_socket)
        send_str_length_and_message(id_message, user_socket)
        send_str_length_and_message(org_public_key, user_socket)

        number_of_employees = len(user["employees"])  # Tell server how many employees the organization has
        num_employees_msg = str(number_of_employees).encode(FORMAT)
        num_employees_msg += b' ' * (HEADER - len(num_employees_msg))
        user_socket.send(num_employees_msg)
        for employee in user.get("employees"):  # Send info of each employee separately
            send_str_length_and_message(employee.get("id"), user_socket)
            send_str_length_and_message(employee.get("role"), user_socket)
        if user.get("org_type") == "Bank":
            while user["connected"]:
                msg_length = user_socket.recv(HEADER).decode(FORMAT)
                sending = user["send_info"]["sending"]
                org_name = user.get("name")
                if msg_length:
                    if not sending:
                        sender_length = int(msg_length)
                        sender = user_socket.recv(sender_length)
                        sender = sender.decode(FORMAT)
                        msg_length = user_socket.recv(HEADER).decode(FORMAT)
                        msg_length = int(msg_length)
                        msg = user_socket.recv(msg_length)
                        priv_key = importKey(user["keys"].get("private"))
                        decrypted_msg = decrypt(msg, priv_key)
                        decrypted_msg = decrypted_msg.decode(FORMAT)
                        print("\n")
                        print("//////////////////////////////////////////////////////////////////////////////////////")
                        print(f"{org_name} has received a message: ")
                        print(f"[{sender}] {decrypted_msg}")
                        print("//////////////////////////////////////////////////////////////////////////////////////")
                    elif sending:
                        key_length = int(msg_length)
                        key = user_socket.recv(key_length)
                        user["send_info"]["pub_key"] = importKey(key)
            # IF BANK, STAY CONNECTED
            # Bank should listen for msg from server saying what is about to happen
            # If 0 -> Bank Transfer, if 1 -> Disbursal, if 2 -> New Account
            # Recv relevant info for that option
            # Check if everything is valid (accounts exist and enough money)
            # Make relevant updates to internal database (dictionary)
            # Send message to server to let know if everything was successful
            # pass
    user["socket"] = None


def end_connection(user):
    """ Disconnects user from server

    Sends server a disconnect message ("2") and sets "Connected" to False, causing the loop in start_connection(),
    to end and the thread to be stopped.

    :param user: A dictionary containing all info about the user of this thread
    :return: None
    """
    user["socket"].send(bytes(f"2", FORMAT))
    user["connected"] = False


def send(message, recipient, sender, opt):
    """ Sends message from current client to some other client

    Send() first tells server if message will be sent to someone using ID or Name and then sends said ID or name.
    Script then waits till server sends recipient's public key for encryption.
    It then encrypts the message and sends it to the server.

    :param message: Message string to be sent to recipient
    :param recipient: Recipient client's ID or Name
    :param sender: Sender client's dictionary containing all info about the client
    :param opt: integer indicating if message recipient is in ID format or Name format, 0 for ID and 1 for Name
    :return: None
    """
    sender["send_info"]["sending"] = True
    sender_socket = sender["socket"]
    option_msg = bytes(f"{opt}", FORMAT)
    sender_socket.send(option_msg)
    recipient_msg = f"{recipient}"
    send_str_length_and_message(recipient_msg, sender_socket)
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
    """ Sends server the length of the message, followed by the message itself

    This method is mostly to avoid repetitive code in other parts of the script.
    The server needs to know the length of a message to be able to receive it. Turns string into bytes using FORMAT.
    Then gets the length of that byte-string. Message gets padded to a preset length (HEADER).
    The server can receive that and then know how many bytes to receive. The method then sends the message.

    :param message: string message to be sent
    :param sender_socket: socket through which length and message must be set
    :return: None
    """
    bmessage = bytes(f"{message}", FORMAT)
    msg_length = len(bmessage)
    send_length = str(msg_length).encode(FORMAT)
    send_length += b' ' * (HEADER - len(send_length))
    sender_socket.send(send_length)
    sender_socket.send(bmessage)


def send_byte_length_and_message(message, sender_socket):
    """ Same as send_str_length_and_message() but without the string to bytes step

    SEE send_str_length_and_message().
    Only difference is that the message doesn't need to be made into bytes

    :param message: byte message to be sent
    :param sender_socket: socket through which length and message must be set
    :return: None
    """
    msg_length = len(message)
    send_length = str(msg_length).encode(FORMAT)
    send_length += b' ' * (HEADER - len(send_length))
    sender_socket.send(send_length)
    sender_socket.send(message)


def load_client(load_option):
    """ Loads client JSON files and saves them

    Opens a file picker to load a client's json file and save it to a dictionary.
    Also initializes various other values for the client:
    ["send_info"] is necessary for the sending process to work
        ["sending"] is a state variable to indicate if client is in the process of sending
        ["pub_key"] is the public key of the user you are sending a message to
    ["type"] is a variable to distinguish between [User] and [Organization]
    ["connected"] is used to keep a connected user's thread looping
    IF load_option is "User":
        New RSA key pair is made and saved as well (Keys of length KEYSIZE)
    IF load_option is "Organization:
        Multiple organizations are initialized with 1 json file, so they are looped through

    :param load_option: String used to identify between [User] and [Organization] during the load process. Can be "User"
                        or "Organization"
    :return: A dictionary of the newly loaded client. Mostly for menuing purposes.
    """
    filepath = askopenfilename()
    if load_option == "User":
        client_file = open(filepath)
        client_info = json.load(client_file)
        # print("Would you like to generate new keys? (y/n):")
        # user_input = input("Please type your option:") # we need save to json functionality
        user_input = "y"
        if user_input == "y":
            pub, pri = newkeys(KEYSIZE)  # here's new keys generated
            client_info["person"]["keys"]["private"] = exportKey(pri)
            client_info["person"]["keys"]["public"] = exportKey(pub)
            # with open(filepath, 'w') as fp:
            #     json.dump(client_info, fp)
        else:
            pass
        client_info["send_info"] = {"sending": False, "pub_key": None}
        client_info["type"] = "User"
        client_info["connected"] = False
        client = client_info
        clients.append(client)
        client_name = client_info["person"]["name"]
        print(f"{client_name} loaded & selected")
        return client
    elif load_option == "Organizations":
        org_file = open(filepath)
        org_info = json.load(org_file)
        for org in org_info["organizations"]:
            pub, pri = newkeys(KEYSIZE)  # here's new keys generated
            org["keys"]["private"] = exportKey(pri)
            org["keys"]["public"] = exportKey(pub)
            org["type"] = "Organization"
            org["send_info"] = {"sending": False, "pub_key": None}
            org["connected"] = False
            organizations.append(org)
            org_name = org.get("name")
            print(f"Loaded {org_name}")
        return org_info


def update_clients(cli_data):
    with open( BASE_DIR +'\\json\\organizations_config.json') as org_file:
        data = json.load(org_file)

    for org in data["organizations"]:
        if org['org_type'] == "Bank" and cli_data is not None:
            org["clients"] = cli_data

    with open(BASE_DIR+'\\json\\organizations_config.json',
              'w') as org_file:
        json.dump(data, org_file, indent=4)

    return data


def transfer(from_acc, to_acc, amount, from_pass):
    from_valid = False
    to_valid = False

    with open(BASE_DIR + '\\json\\organizations_config.json') as org_file:
        data = json.load(org_file)

    for org in data["organizations"]:
        if org['org_type'] == "Bank":
            clients_data = []

            for cli in org["clients"]:
                clients_data.append(cli)
                balance = cli.get("balance")

                if cli.get("account_number") == from_acc and float(balance) > amount and cli.get(
                        "password") == from_pass:
                    name = cli.get('name')
                    password = cli.get("password")
                    acc_num = cli.get("account_number")
                    balan = str(float(balance) - amount)

                    updated_cli = {"name": name, "password": password, "account_number": acc_num, "balance": balan}
                    clients_data.remove(cli)
                    clients_data.append(updated_cli)
                    from_valid = True

                elif cli.get("account_number") == to_acc:
                    name = cli.get('name')
                    password = cli.get("password")
                    acc_num = cli.get("account_number")
                    balan = str(float(balance) + amount)

                    updated_cli = {"name": name, "password": password, "account_number": acc_num, "balance": balan}
                    clients_data.remove(cli)
                    clients_data.append(updated_cli)
                    to_valid = True

            if from_valid and to_valid:
                return clients_data

            else:
                return "Invalid Transfer"


def disbursal(from_acc, amount, from_pass):
    from_valid = False

    with open(BASE_DIR + '\\json\\organizations_config.json') as org_file:
        data = json.load(org_file)

    for org in data["organizations"]:
        if org['org_type'] == "Bank":
            clients_data = []

            for cli in org["clients"]:
                clients_data.append(cli)
                balance = cli.get("balance")

                if cli.get("account_number") == from_acc and float(balance) > amount and cli.get(
                        "password") == from_pass:
                    name = cli.get('name')
                    password = cli.get("password")
                    acc_num = cli.get("account_number")
                    balan = str(float(balance) - amount)

                    updated_cli = {"name": name, "password": password, "account_number": acc_num, "balance": balan}
                    clients_data.remove(cli)
                    clients_data.append(updated_cli)
                    from_valid = True

            if from_valid:
                return clients_data

            else:
                return "Invalid Disbursal"


def deposit(to_acc, amount, to_pass):
    to_valid = False

    with open(BASE_DIR + '\\json\\organizations_config.json') as org_file:
        data = json.load(org_file)

    for org in data["organizations"]:
        if org['org_type'] == "Bank":
            clients_data = []

            for cli in org["clients"]:
                clients_data.append(cli)
                balance = cli.get("balance")

                if cli.get("account_number") == to_acc and float(balance) > 0 and cli.get("password") == to_pass:
                    name = cli.get('name')
                    password = cli.get("password")
                    acc_num = cli.get("account_number")
                    balan = str(float(balance) + amount)

                    updated_cli = {"name": name, "password": password, "account_number": acc_num, "balance": balan}
                    clients_data.remove(cli)
                    clients_data.append(updated_cli)
                    to_valid = True

            if to_valid:
                return clients_data

            else:
                return "Invalid Deposit"


def check_account_name(acc_name):
    already_exists = False

    with open(BASE_DIR + '\\json\\organizations_config.json') as org_file:
        data = json.load(org_file)

    for org in data["organizations"]:
        if org['org_type'] == "Bank":

            for cli in org["clients"]:
                if cli.get("name") == acc_name:
                    already_exists = True

                else:
                    already_exists = False

    if already_exists:
        return "Yes"

    else:
        return "No"


def check_account_pass(acc_name, your_pass):
    correct_pass = False

    with open(BASE_DIR + '\\json\\organizations_config.json') as org_file:
        data = json.load(org_file)

    for org in data["organizations"]:
        if org['org_type'] == "Bank":
            clients_data = []

            for cli in org["clients"]:
                if cli.get("name") == acc_name and cli.get("password") == your_pass:
                    correct_pass = True

                else:
                    correct_pass = False

    if correct_pass:
        return "Yes"

    else:
        return "No"


def add_new_account(acc_name, acc_pass):
    with open(BASE_DIR + '\\json\\organizations_config.json') as org_file:
        data = json.load(org_file)

    for org in data["organizations"]:
        if org['org_type'] == "Bank":
            clients_data = []

            for cli in org["clients"]:
                clients_data.append(cli)

            auto_acc = generate_unique_acc()
            new_acc = {"name": acc_name, "password": acc_pass, "account_number": auto_acc, "balance": "0"}
            clients_data.append(new_acc)
            return clients_data, auto_acc


def generate_unique_acc():
    with open(BASE_DIR + '\\json\\organizations_config.json') as org_file:
        data = json.load(org_file)

    acc_num = randint(600000, 10000000)

    for org in data["organizations"]:
        if org['org_type'] == "Bank":

            for cli in org["clients"]:
                if cli.get("account_number") == acc_num:
                    generate_unique_acc()
                else:
                    return str(acc_num)


def make_new_account(acc_name, acc_pass):
    with open(BASE_DIR + '\\json\\organizations_config.json') as org_file:
        data = json.load(org_file)

    for org in data["organizations"]:
        if org['org_type'] == "Bank":
            clients_data = []

            for cli in org["clients"]:
                clients_data.append(cli)

            auto_acc = generate_unique_acc()
            new_acc = {"name": acc_name, "password": acc_pass, "account_number": auto_acc, "balance": "0"}
            clients_data.append(new_acc)
            return clients_data, auto_acc


def start():
    """ Main script look and terminal UI

    This method is used to control the actions in the client script.
    currently_selected_client: The client that will perform the chosen action. The action options are restricted by the
    options of the currently_selected_client. Can be a "User" or an "Organization"
    The script waits for an action to be chosen in the terminal.
    Action options:
        1. Load - Asks script user if they want to load a User or an Organization and runs load_client(). If the script
                  user loads a "User", then currently_connected_client is set to the newly loaded client.
        2. Select - Used to choose a currently_selected_client.
        3. Connect - Connects the currently_selected_client to the server by running start_connection().
        4. Send - Prompts script user to select the following: "How to send", "Who to send to" and "What to send"
                  Then runs send() with the inputs given.
        5. Disconnect - Disconnects the currently_selected_client from the server by running end_connection().

    TODO Add more options for linking Clients to Organization Employee ID's
    TODO Add the following options: Bank Transfer (user), Disbursal (user), Make Account (user), Deposit (Bank)

    :return: None
    """
    running = True
    currently_selected_client = None
    # currently_selected_organiz = None

    while running:
        print()
        if not currently_selected_client is None:
            menu_type = currently_selected_client["type"]
            connected = currently_selected_client["connected"]
            if menu_type == "User":
                crnt_client_name = currently_selected_client["person"].get("name")
                print(f"Current user: {crnt_client_name}")
                if connected:
                    print("Action options: <1> Load, <2> Select, <4> Send, <5> Disconnect, <6> Transfer, "
                          "<7> Disbursal, <8> Deposit, <9> Make Account")
                elif not connected:
                    print("Action options: <1> Load, <2> Select, <3> Connect")
            elif menu_type == "Organization":
                crnt_client_name = currently_selected_client["name"]
                print(f"Current user: {crnt_client_name}")
                if connected:
                    print("Action options: <1> Load, <2> Select") #add disconnect option
                elif not connected:
                    print("Action options: <1> Load, <2> Select, <3> Connect")
        else:
            menu_type = "None"
            connected = False
            print("Action options: <1> Load, <2> Select")

        # Request Action: 1=Load, 2=Select, 3=Connect, 4=Send, 5=Disconnect --------------------------------------------
        user_input = input("Please type number of action: ")
        if user_input == "1":
            user_input = "Load"
        elif user_input == "2":
            user_input = "Select"
        elif user_input == "3":
            user_input = "Connect"
        elif user_input == "4":
            user_input = "Send"
        elif user_input == "5":
            user_input = "Disconnect"
        elif user_input == "6":
            user_input = "Transfer"
        elif user_input == "7":
            user_input = "Disbursal"
        elif user_input == "8":
            user_input = "Deposit"
        elif user_input == "9":
            user_input = "Make Account"

        # Load option --------------------------------------------------------------------------------------------------
        if user_input == "Load" and (menu_type == "None" or menu_type == "User" or menu_type == "Organization"):
            print("Load options: <1> User, <2> Organizations")
            load_type = input("Please type option: ")
            if load_type == "1":
                load_type = "User"
            elif load_type == "2":
                load_type = "Organizations"
            if load_type == "User":
                client = load_client(load_type)
                currently_selected_client = client
            elif load_type == "Organizations":
                organization = load_client(load_type)
                #currently_selected_client = organization
            else:
                print("Invalid option.")

        # Select option ------------------------------------------------------------------------------------------------
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

        # Connect option -----------------------------------------------------------------------------------------------
        elif user_input == "Connect" and (menu_type == "User" or menu_type == "Organization") and not connected:
            if menu_type == "Organization":
                if currently_selected_client.get("org_type")=="Bank":
                    thread = threading.Thread(target=start_connection, args=[currently_selected_client])
                    thread.start()
                    connected_clients.append((currently_selected_client, thread))
                    currently_selected_client["connected"] = True
                    print(f"{crnt_client_name} has connected!")
                else:
                    print(f"{crnt_client_name} is not a bank! Thus it doesn't connect")
            else:
                thread = threading.Thread(target=start_connection, args=[currently_selected_client])
                thread.start()
                connected_clients.append((currently_selected_client, thread))
                currently_selected_client["connected"] = True
                print(f"{crnt_client_name} has connected!")

        # Send option --------------------------------------------------------------------------------------------------
        elif user_input == "Send" and (menu_type == "User") and connected:
            if not currently_selected_client is None:
                option = input("Send using <1> ID or <2> Name>: ")
                if option == "1":
                    option = 0
                elif option == "2":
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

        # Disconnect option --------------------------------------------------------------------------------------------
        elif user_input == "Disconnect" and (menu_type == "User") and connected:
            end_connection(currently_selected_client)
            for x in connected_clients:
                if x[0] is currently_selected_client:
                    connected_clients.remove(x)
            currently_selected_client = None
            print(f"{crnt_client_name} has disconnected!")

        # Transfer option ----------------------------------------------------------------------------------------------
        elif user_input == "Transfer" and (menu_type == "User") and connected:
            from_acc = input("Enter your account number: ")
            from_pass = input("Enter your password: ")
            to_acc = input("Enter the account to transfer: ")
            amount = input("Enter the amount of money: ")
            amount = float(amount)
            clients_data_info = transfer(from_acc, to_acc, amount, from_pass)

            if clients_data_info == "Invalid Transfer":
                print("Invalid Transfer")

            else:
                update_clients(clients_data_info)
                print(str(amount) + " Euros Transferred from '" + from_acc + "' to '" + to_acc)

        # Disbursal option ---------------------------------------------------------------------------------------------
        elif user_input == "Disbursal" and (menu_type == "User") and connected:
            from_acc = input("Enter your account number: ")
            from_pass = input("Enter your password: ")
            amount = input("Enter the amount of money: ")
            amount = float(amount)
            clients_data_info = disbursal(from_acc, amount, from_pass)

            if clients_data_info == "Invalid Disbursal":
                print("Invalid Disbursal")

            else:
                update_clients(clients_data_info)
                print(str(amount) + " Euros deducted from '" + from_acc + "'")

        # Deposit option -----------------------------------------------------------------------------------------------
        elif user_input == "Deposit" and (menu_type == "User") and connected:
            to_acc = input("Enter your account number: ")
            to_pass = input("Enter your password: ")
            amount = input("Enter the amount of money: ")
            amount = float(amount)
            clients_data_info = deposit(to_acc, amount, to_pass)

            if clients_data_info == "Invalid Deposit":
                print("Invalid Deposit")

            else:
                update_clients(clients_data_info)
                print(str(amount) + " Euros deposited into '" + to_acc + "'")

        # Make Account -------------------------------------------------------------------------------------------------
        elif user_input == "Make Account" and (menu_type == "User") and connected:
            acc_name = input("Enter your name: ")
            result_check_name = check_account_name(acc_name)

            if result_check_name == "Yes":
                print("Account name already exists")
                print("Action options: <1> Yes, <2> No")
                is_this_you = input("Is this your account? ")

                if is_this_you == "1":
                    your_pass = input("Enter your password: ")
                    result_pass = check_account_pass(acc_name, your_pass)

                    if result_pass == "Yes":
                        print("Action options: <1> Yes, <2> No")
                        new_acc = input("Would you like to add another account? ")

                        if new_acc == "1":
                            clients_data_info, auto_acc = add_new_account(acc_name, your_pass)
                            update_clients(clients_data_info)
                            print("Your new account number is '" + auto_acc + "'")

                    else:
                        print("Wrong Password")

                else:
                    acc_pass = input("Create your password: ")
                    clients_data_info, auto_acc = make_new_account(acc_name, acc_pass)
                    update_clients(clients_data_info)
                    print("Your account number is: '" + auto_acc + "'")

            else:
                acc_pass = input("Create your password: ")
                clients_data_info, auto_acc = make_new_account(acc_name, acc_pass)
                update_clients(clients_data_info)
                print("Your account number is: '" + auto_acc + "'")

        # No valid inputs ----------------------------------------------------------------------------------------------
        else:
            print("Invalid input")


start()
