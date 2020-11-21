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
    sender_ID = sender.get("user_ID")
    message = bytes(f"[{sender_ID}] {msg}", FORMAT)
    msg_length = len(message)
    send_length = str(msg_length).encode(FORMAT)
    send_length += b' ' * (HEADER - len(send_length))
    recipient["user_conn"].send(send_length)
    recipient["user_conn"].send(message)
    return True


def handle_client(user):
    user_ID = user["user_ID"]
    conn = user["user_conn"]
    addr = user["user_addr"]
    print(f"[NEW CONNECTION] {user_ID} connected.")
    for msg_item in msg_bank:
        msg, msg_receiver, msg_sender = msg_item
        if msg_receiver == user_ID:
            send_msg(msg, user, msg_sender)

    connected = True
    while connected:
        msg_receiver_ID = conn.recv(USER_ID_LENGTH).decode(FORMAT)
        msg_length = conn.recv(HEADER).decode(FORMAT)
        if msg_length:
            msg_length = int(msg_length)
            msg = conn.recv(msg_length).decode(FORMAT)
            if msg == DISCONNECT_MESSAGE:
                active_users.remove(user)
                connected = False
            print(f"[{addr}] {msg}")
        msg_sent = False
        for active_user in active_users:
            if active_user.get("user_ID") == msg_receiver_ID:
                msg_sent = send_msg(msg, active_user, user)
                break
        if not msg_sent:
            msg_bank.append((msg, msg_receiver_ID, user))

    conn.close()


def start():
    server.listen()
    print(f"[LISTENING] Server is listening on {SERVER}")
    while True:
        conn, addr = server.accept()
        ID = f"{conn.recv(USER_ID_LENGTH).decode(FORMAT)}"
        user = {
            "user_ID": ID,
            "user_conn": conn,
            "user_addr": addr}
        if not known_users.__contains__(user):
            known_users.append(user)
            user_ID = user["user_ID"]
            print(f"[NEW USER] {user_ID} has registered")
            #print(known_users[user_ID])
        active_users.append(user)
        thread = threading.Thread(target=handle_client, args=[user])
        thread.start()
        print(f"[ACTIVE CONNECTIONS] {threading.activeCount() - 1}")


print("[STARTING] Server is starting...")
start()
