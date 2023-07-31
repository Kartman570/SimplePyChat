import socket
import threading
import time


HOST = "127.0.0.1"
PORT = 12345
KEEP_ALIVE_SEC = 5

is_running = True
clients = {}
logs = []


def send_everyone(user_from: str, text: str) -> None:
    for nick, client_info in clients.items():
        message = user_from + text
        message = str(len(user_from)) + ":" + message
        client_info["connection"].sendall(message.encode())


def send_everyone_except(user_from: str, text: str, user_except: str) -> None:
    for nick, client_info in clients.items():
        if nick != user_except:
            message = user_from + text
            message = str(len(user_from)) + ":" + message
            client_info["connection"].sendall(message.encode())


def send_to(user_from: str, text: str, user_target: str) -> None:
    message = user_from + text
    message = str(len(user_from)) + ":" + message
    clients[user_target]["connection"].sendall(message.encode())


def new_client(connection: socket.socket, addr) -> None:
    nickname = None
    client_info = {"address": addr,
                   "connection": connection,
                   "last_keepalive": time.time(),
                   "is_active": True}
    try:
        while is_running and client_info["is_active"]:
            data = connection.recv(1024)
            if not data:
                break

            recieved = data.decode()
            delimiter, message = recieved.split(":", 1)
            nickname = message[:int(delimiter)]
            message = message[int(delimiter):]

            if message == "keepalive:":
                clients[nickname]['last_keepalive'] = time.time()
                continue

            logs.append({
             "time": time.strftime("%d.%m.%Y %H:%M:%S", time.localtime()),
             "addr": str(addr),
             "nickname": nickname,
             "message": message
             })
            if nickname == "system":
                nickname = message
                clients[nickname] = client_info
                send_everyone("server", nickname + " joined")
                print(f"{nickname} joined")
                continue
            if message == "quit:":
                break
            if message == "online:":
                send_to("server", ", ".join(clients), nickname)
                continue

            print(f"{nickname} - {message}")
            send_everyone_except(nickname, message, nickname)
    except socket.error:
        print(f"Lost connection to {nickname}")
    finally:
        send_everyone("server", nickname + " left")
        print(f"{nickname} Left")
        if nickname in clients:
            del clients[nickname]
        connection.close()


def console(s: socket.socket) -> None:
    print("Succesfuly started.")
    help_msg = ('''
     commands:
     logs: -u %username%   show all messages from %username%
     logs: -t %time or date%   show all messages at time or date
     logs: -a   show all messages
     online:   show who is connected now
     help:   shwo this message
     stop:   send deauth to online users and shutdown server
     ''')
    print(help_msg)
    while True:
        command = input()
        if command == "help:":
            print(help_msg)
            continue
        if command == "stop:":
            while command != "Y" and command != "N":
                command = input("SHUTDOWN SERVER\nARE YOU SURE? Y/N").upper()
            if command == "N":
                continue
            print("SHUTDOWN SERVER")
            for nick, client_info in clients.items():
                send_everyone("server", "SHUTDOWN")
            is_running = False
            break
        if command == "online:":
            for nick, client_info in clients.items():
                print(nick + str(client_info["address"]))
            continue
        if command.startswith("logs:"):
            command_parts = command.split()
            if len(command_parts) == 1:
                print("""Missing argument. To see logs use arguments:
                logs: -u %username%   show all messages from %username%
                logs: -t %time or date%   show all messages at time or date
                logs: -a   show all messages
                """)
            else:
                argument = command_parts[1]
                value = command_parts[2] if len(command_parts) > 2 else None
                if value == "":
                    print("Missing argument`s value")
                if argument == "-u":
                    for log in logs:
                        if log['nickname'] == value:
                            print(f"{log['time']};{log['addr']};{log['nickname']};{log['message']}")
                elif argument == "-t":
                    for log in logs:
                        if value in log['time']:
                            print(f"{log['time']};{log['addr']};{log['nickname']};{log['message']}")
                elif argument == "-a":
                    for log in logs:
                        print(f"{log['time']};{log['addr']};{log['nickname']};{log['message']}")
                else:
                    print("Invalid command")
            continue
        send_everyone("server", command)


def accept_thread(s: socket.socket) -> None:
    while is_running:
        conn, addr = s.accept()
        threading.Thread(target=new_client, args=(conn, addr), daemon=True).start()


with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    s.bind((HOST, PORT))
    s.listen()

    threading.Thread(target=accept_thread, args=(s,), daemon=True).start()
    console(s)
    s.close()
