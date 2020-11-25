import socket
import threading

HEADER = 64
PORT = 5050
SERVER = socket.gethostbyname(socket.gethostname())
ADDR = (SERVER, PORT)
FORMAT = 'utf-8'
DISCONNECT_MESSAGE = "!DISCONNECT"
USER_ID_LENGTH = 36

known_users = []
active_users = []
msg_bank = []

server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.bind(ADDR)


def send_msg(msg, recipient, sender):
    sender_name = sender.get("user_name")
    message = bytes(f"[{sender_name}] {msg}", FORMAT)
    msg_length = len(message)
    send_length = str(msg_length).encode(FORMAT)
    send_length += b' ' * (HEADER - len(send_length))
    recipient["user_conn"].send(send_length)
    recipient["user_conn"].send(message)
    return True


def receive_padded_msg(connection):
    msg_length = connection.recv(HEADER).decode(FORMAT)
    if msg_length:
        msg_length = int(msg_length)
        msg = connection.recv(msg_length).decode(FORMAT)
        return msg


def handle_client(user):
    user_name = user["user_name"]
    user_ID = user["user_ID"]
    conn = user["user_conn"]
    addr = user["user_addr"]
    print(f"[NEW CONNECTION] {user_name} connected.")
    # Check for messages user got while offline
    for msg_item in msg_bank:
        msg, msg_receiver, msg_sender = msg_item
        if msg_receiver == user:
            send_msg(msg, user, msg_sender)
    # Run loop while user is online
    connected = True
    while connected:
        option = int(conn.recv(1).decode(FORMAT))  # Will recipient be ID or name?
        if option == 0:
            msg_receiver_ID = conn.recv(USER_ID_LENGTH).decode(FORMAT)
            receiver = None
            for x in known_users:
                if x.get("user_ID") == msg_receiver_ID:
                    receiver = x
        elif option == 1:
            msg_receiver_name = receive_padded_msg(conn)
            receiver = None
            for x in known_users:
                if x.get("user_name") == msg_receiver_name:
                    receiver = x
        # Send key first!
        receiver_pub_key = receiver.get("user_key").encode(FORMAT)
        msg_length = len(receiver_pub_key)
        send_length = str(msg_length).encode(FORMAT)
        send_length += b' ' * (HEADER - len(send_length))
        conn.send(send_length)
        conn.send(receiver_pub_key)
        msg = receive_padded_msg(conn)

        print(f"[{addr}] {msg}")
        if msg == DISCONNECT_MESSAGE:
            active_users.remove(user)
            connected = False
        if receiver is None and connected is True:
            print("Recipient user unknown")
            break
        msg_sent = False
        # Check if message recipient is online.
        # Yes - Send to them. No - Save message for when they come online.
        for active_user in active_users:
            if active_user is receiver:
                msg_sent = send_msg(msg, active_user, user)
        if not msg_sent:
            msg_bank.append((msg, receiver, user))
    conn.close()


def start():
    server.listen()
    print(f"[LISTENING] Server is listening on {SERVER}")
    while True:
        conn, addr = server.accept()
        ID = f"{conn.recv(USER_ID_LENGTH).decode(FORMAT)}"
        name = receive_padded_msg(conn)
        key = receive_padded_msg(conn)
        user = {
            "user_name": name,
            "user_ID": ID,
            "user_key": key,
            "user_conn": conn,
            "user_addr": addr}
        if not known_users.__contains__(user):
            known_users.append(user)
            user_ID = user["user_ID"]
            print(f"[NEW USER] {user_ID} has registered")
        active_users.append(user)
        thread = threading.Thread(target=handle_client, args=[user])
        thread.start()
        print(f"[ACTIVE CONNECTIONS] {len(active_users)}")


print("[STARTING] Server is starting...")
start()
