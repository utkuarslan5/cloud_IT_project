import socket
import threading

HEADER = 64  # Default length for a message that indicates next message's length
PORT = 5050
SERVER = socket.gethostbyname(socket.gethostname())
ADDR = (SERVER, PORT)
FORMAT = 'utf-8'

known_users = []
active_users = []
organizations = []
msg_bank = []

server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.bind(ADDR)


def send_padded_str(msg, recipient):
    """ Sends padded message through recipient socket

    Sends padded messages to the recipient client.

    :param msg: String message to be sent to recipient
    :param recipient: Recipient client dictionary
    :return: True
    """
    msg_length = len(msg)
    msg_length = str(msg_length).encode(FORMAT)
    msg_length += b' ' * (HEADER - len(msg_length))
    recipient["user_conn"].send(msg_length)
    msg = bytes(msg, FORMAT)
    recipient["user_conn"].send(msg)
    return True


def send_padded_bytes(msg, recipient):
    """ Sends padded message through recipient socket

    Sends padded messages to the recipient client.

    :param msg: Bytes message to be sent to recipient
    :param recipient: Recipient client dictionary
    :return: True
    """
    msg_length = len(msg)
    msg_length = str(msg_length).encode(FORMAT)
    msg_length += b' ' * (HEADER - len(msg_length))
    recipient["user_conn"].send(msg_length)
    recipient["user_conn"].send(msg)
    return True


def receive_padded_str_msg(connection):
    """ Receive a string message whose length wasn't pre-determined

    Server needs to know how long a message will be to receive it. This method combines the "how long will the msg be"
    and then the message getting methods in one reusable block.

    :param connection: The connection with a client socket through which the message will be sent
    :return: The sent message as a string
    """
    msg_length = connection.recv(HEADER).decode(FORMAT)
    if msg_length:
        msg_length = int(msg_length)
        msg = connection.recv(msg_length).decode(FORMAT)
        return msg


def receive_padded_byte_msg(connection):
    """ Receive a byte string message whose length wasn't pre-determined

    Identical to receive_padded_str_msg(), except the received message isn't converted from byte to string (because the
    original client message was a byte string like with RSA keys)

    :param connection:
    :return:
    """
    msg_length = connection.recv(HEADER).decode(FORMAT)
    if msg_length:
        msg_length = int(msg_length)
        msg = connection.recv(msg_length)
        return msg


def handle_client(user):
    """ Handles a connection to a client

    When a user connects, this method is started on a thread. It waits for actions that the user wants to do.
    First the method checks for messages that should have been sent to the user by going through the msg_bank.
    Then the server waits to hear which option the user wants to use.
    Action options:
    0. Send message to someone using their ID
    1. Send message to someone using their Name
    2. Disconnect user from the server

    If a user wants to send a message to someone, the server gets that persons public key and sends it to the user first
    for encryption of the message. The server then receives the encrypted message and checks if the recipient is online.
    If the recipient is online, it sends the encrypted message and sender name. Otherwise it saves the message,
    recipient_name and sender_name in a msg_bank for when the recipient connects.

    Closes the socket when the user disconnects.

    #TODO handle_client() only handles "User" clients now. Add initial check for organizations, also need functionality
    #TODO for step 3 actions here

    :param user: A dictionary of the user that will be handled in this thread.
    :return: None
    """
    user_name = user["user_name"]
    user_ID = user["user_ID"]
    conn = user["user_conn"]
    addr = user["user_addr"]
    print(f"[NEW CONNECTION] {user_name} connected.")
    if not user["key_changed"]:
        for msg_item in msg_bank:
            msg, msg_receiver, msg_sender = msg_item
            if msg_receiver == user_name:
                send_padded_str(msg_sender, user)
                send_padded_bytes(msg, user)
    else:
        user["key_changed"] = False
    connected = True
    while connected:
        option = int(conn.recv(1).decode(FORMAT))
        allowed = False
        if option == 0:
            msg_receiver_ID = receive_padded_str_msg(conn)
            receiver = None
            for x in known_users:
                if x.get("user_ID") == msg_receiver_ID:
                    receiver = x
                    allowed = check_role_requirements(user, receiver)
        elif option == 1:
            msg_receiver_name = receive_padded_str_msg(conn)
            receiver = None
            for x in known_users:
                if x.get("user_name") == msg_receiver_name:
                    receiver = x
                    allowed = check_role_requirements(user, receiver)
        elif option == 2:
            active_users.remove(user)
            connected = False
            print(f"[DISCONNECTION] {user_name} disconnected.")
            print(f"[ACTIVE CONNECTIONS] {len(active_users)}")
            
        elif option == 3:
            check = False
            org_name = receive_padded_str_msg(conn)
            org_id = receive_padded_str_msg(conn)
            for org in organizations:
                if org["user_name"] == org_name:
                    for emp in org["employees"]:
                        if emp["emp_p_id"] == org_id:
                            org_role = emp["emp_role"]
                            org_emp_id = emp["emp_id"]
                            check = True

            if check != True:
                print("Invalid linking")
            else:
                user["user_employer"] = org_name
                user["user_employee_id"] = org_emp_id
                user["user_role"] = org_role
                print("The user is linked")

        if (option == 0 or option == 1):  # Message sending code
            if allowed:
                allowed_msg = "1".encode(FORMAT)
                send_padded_bytes(allowed_msg, user)
                receiver_pub_key = receiver.get("user_key")
                msg_length = len(receiver_pub_key)
                send_length = str(msg_length).encode(FORMAT)
                send_length += b' ' * (HEADER - len(send_length))
                conn.send(send_length)
                conn.send(receiver_pub_key)
                msg = receive_padded_byte_msg(conn)
                msg_receiver_name = receiver.get("user_name")
                print(f"[{user_name}] sent [{msg_receiver_name}] a message")
                print(f"{msg}")
                if receiver is None and connected is True:
                    print("Recipient user unknown")
                    break
                msg_sent = False
                for active_user in active_users:
                    if active_user is receiver:
                        send_padded_str(user["user_name"], active_user)
                        msg_sent = send_padded_bytes(msg, active_user)
                if not msg_sent:
                    msg_bank.append((msg, receiver["user_name"], user["user_name"]))
            elif not allowed:
                allowed_msg = "0".encode(FORMAT)
                send_padded_bytes(allowed_msg, user)
    conn.close()


def handle_bank(organization):
    org_name = organization["user_name"]
    org_ID = organization["user_ID"]
    conn = organization["user_conn"]
    addr = organization["user_addr"]
    organization["connected"] = True
    print(f"[NEW CONNECTION] {org_name} connected.")

    while organization["connected"]:
        option = int(conn.recv(1).decode(FORMAT))

        if option == 0:
            msg_receiver_ID = receive_padded_str_msg(conn)
            receiver = None
            for x in known_users:
                if x.get("user_ID") == msg_receiver_ID:
                    receiver = x
        elif option == 1:
            msg_receiver_name = receive_padded_str_msg(conn)
            receiver = None
            for x in known_users:
                if x.get("user_name") == msg_receiver_name:
                    receiver = x
        elif option == 2:
            organization["connected"] = False
            active_users.remove(organization)
            print(f"[DISCONNECTION] {org_name} disconnected.\n")

            print(f"[ACTIVE CONNECTIONS] {len(active_users)}")

        if (option == 0 or option == 1):  # Message sending code
            receiver_pub_key = receiver.get("user_key")
            msg_length = len(receiver_pub_key)
            send_length = str(msg_length).encode(FORMAT)
            send_length += b' ' * (HEADER - len(send_length))
            conn.send(send_length)
            conn.send(receiver_pub_key)
            msg = receive_padded_byte_msg(conn)
            msg_receiver_name = receiver.get("user_name")
            print(f"[{org_name}] sent [{msg_receiver_name}] a message")
            print(f"{msg}")
            if receiver is None and organization["connected"] is True:
                print("Recipient user unknown")
                break
            msg_sent = False
            for active_user in active_users:
                if active_user is receiver:
                    send_padded_str(organization["user_name"], active_user)
                    msg_sent = send_padded_bytes(msg, active_user)
            if not msg_sent:
                msg_bank.append((msg, receiver["user_name"], organization["user_name"]))

    conn.close()


def check_role_requirements(sender, receiver):
    """
       Code simply checks for every role whether the sender's rank is <= to the receiver's rank
    """
    if sender["user_role"] == "Guest" and receiver["user_role"] == "Guest":
        return True
    elif sender["user_role"] == "Guest":
        return False

    if sender["user_role"] == "Manager":
        return True
    elif sender["user_role"] == "Executive" and receiver["user_role"] != "Manager":
        return True
    elif sender["user_role"] == "Employee" and receiver["user_role"] != "Manager" and receiver[
        "user_role"] != "Executive" and sender["user_employer"] == receiver["user_employer"]:
        return True
    elif sender["user_role"] == "Secretary" and receiver["user_role"] == "Secretary" and sender["user_employer"] == \
            receiver["user_employer"]:
        return True
    else:
        return False


def start():
    """ Starts server and listens for new connections

    The server is started and then keeps waiting for users to connect. First it receives a message to know if the
    connection is for a "User" or an "Organization". It then receives messages with all relevant data, and saves it to
    a dictionary.
    If the user had connected before, the server updates the data (in case anything changed).

    #TODO Give organizations a thread and handle them too

    :return: None
    """
    server.listen()
    print(f"[LISTENING] Server is listening on {SERVER}")
    while True:
        conn, addr = server.accept()
        option = int(conn.recv(1).decode(FORMAT))  # Will connection be user (0) or organization (1)?
        if option == 0: #option: user
            ID = receive_padded_str_msg(conn)
            name = receive_padded_str_msg(conn)
            key = receive_padded_byte_msg(conn)
            user = {
                "user_name": name,
                "user_ID": ID,
                "user_employer": None,
                "user_employee_id": None,
                "user_role": "Guest",
                "key_changed": False,
                "user_key": key,
                "user_conn": conn,
                "user_addr": addr}
            known = False
            for x in known_users:
                if x["user_ID"] == ID:
                    known = True
                    x["user_name"] = name
                    x["user_conn"] = conn
                    x["user_addr"] = addr
                    if not x["user_key"] == key:
                        x["user_key"] = key
                        x["key_changed"] = True
                    break
            if not known:
                known_users.append(user)
                print(f"[NEW REGISTRATION] {name} registered")
            active_users.append(user)
            thread = threading.Thread(target=handle_client, args=[user])
            thread.start()
            print(f"[ACTIVE CONNECTIONS] {len(active_users)}")
        elif option == 1: #option: organization
            name = receive_padded_str_msg(conn)
            org_type = receive_padded_str_msg(conn)
            ID = receive_padded_str_msg(conn)
            key = receive_padded_byte_msg(conn)
            number_of_employees = conn.recv(HEADER).decode(FORMAT)
            number_of_employees = int(number_of_employees)
            org_employees = []
            for x in range(number_of_employees):
                employee_ID = receive_padded_str_msg(conn)
                employee_personal_ID = receive_padded_str_msg(conn)
                employee_role = receive_padded_str_msg(conn)
                employee = {
                    "emp_id": employee_ID,
                    "emp_p_id": employee_personal_ID,
                    "emp_role": employee_role
                }
                org_employees.append(employee)

            organization = {
                "user_name": name,
                "user_ID": ID,
                "user_key": key,
                "key_changed": False,
                "employees": org_employees,
                "type": org_type,
                "user_conn": conn,
                "user_addr": addr,
                "connected": True
            }
            known = False
            for x in organizations:
                if x["name"] == name:
                    known = True
                    organizations.remove(x)
                    organizations.append(organization)
                    known_users.remove(x)
                    known_users.append(organization)
                    break
            if not known:
                organizations.append(organization)
                known_users.append(organization)
                print(f"[NEW ORGANIZATION REGISTRATION] {name} registered")
            active_users.append(organization)
            thread = threading.Thread(target=handle_bank, args=[organization])
            thread.start()
            print(f"[ACTIVE CONNECTIONS] {len(active_users)}")



print("[STARTING] Server is starting...")
start()
