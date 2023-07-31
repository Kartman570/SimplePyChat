import socket
import threading
import time


HOST = "127.0.0.1"
PORT = 12345
IS_RUNNING = True
KEEP_ALIVE_SEC = 5
clients = {}
logs = []


def send_everyone(msg: str) -> None:
    for nick, client_info in clients.items():
        client_info["connection"].sendall(msg.encode())


def send_everyone_except(msg: str, except_client: str) -> None:
    for nick, client_info in clients.items():
        if nick != except_client:
            client_info["connection"].sendall(msg.encode())


def send_to(msg: str, target_client: str) -> None:
    clients[target_client]["connection"].sendall(msg.encode())


def new_client(connection: socket.socket, addr) -> None:
    nickname = None
    client_info = {"address": addr, "connection": connection, "last_keepalive": time.time(), "is_active": True}
    try:
        while IS_RUNNING and client_info["is_active"]:
            data = connection.recv(1024)
            if not data:
                break
            message = data.decode()
            nickname, message = message.split(":", 1)
            
            
            if message == "keepalive:":
                clients[nickname]['last_keepalive'] = time.time()
                continue
            
            logs.append(";".join(( \
             time.ctime(time.time()), \
             str(addr), \
             nickname, \
             message \
             )))
            if message == "new_user:":
                clients[nickname] = client_info
                send_everyone("server:" + nickname + " joined")
                print(f"{nickname} joined")
                continue
            if message == "quit:":
                break
            if message == "online:":
                send_to("server:" + ", ".join(clients),nickname)
                continue

            print(f"{nickname} - {message}")
            send_everyone_except(nickname + ":" + message, nickname)
    except socket.error:
        print(f"Lost connection to {nickname}")
    finally:
        send_everyone("server:" + nickname + " left")
        print(f"{nickname} Left")
        if nickname in clients:
            del clients[nickname]
        connection.close()

def console(s : socket.socket) -> None:
    print('''Succesfuly started.
     
     commands:
     logs %username% - show all messages from %username%
     online - show who is connected now
     stop - send deauth to online users and shutdown server
     ''')
    while True:
        command = input()
        if command == "stop":
            print("SHUTDOWN SERVER")
            IS_RUNNING = False
            for nick, client_info in clients.items():
                client_info["connection"].sendall("server:SHUTDOWN".encode())
            break
        if command == "online":
            for nick, client_info in clients.items():
                print(nick + str(client_info["address"]))
            continue
        if command.startswith("logs"):
            _, _, username = command.partition(" ")
            for event in logs:
                if username in event:
                    print(event)
            continue
        send_everyone("server:"+command)

def accept_thread(s : socket.socket) -> None:
    while IS_RUNNING:
        conn, addr = s.accept()
        threading.Thread(target=new_client, args=(conn, addr), daemon=True).start()


with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    s.bind((HOST, PORT))
    s.listen()
    
    console_thread = threading.Thread(target=console, args=(s,), daemon=True)
    console_thread.start()
    
    threading.Thread(target=accept_thread, args=(s,), daemon=True).start()
    
    console_thread.join()
    s.close()
