import socket
import time
import threading
import sys

HOST = "127.0.0.1"
PORT = 12345
KEEP_ALIVE_DELAY = 1

is_running = True
my_nickname = ""
input_text = ""


def send_message(s: socket.socket) -> None:
    global input_text
    while True:
        input_text = input(f"{my_nickname}(you) - ")
        message = my_nickname + input_text
        message = str(len(my_nickname)) + ":" + message
        s.sendall(message.encode())
        if input_text == "quit:":
            is_running = False
            break


def receive_message(s: socket.socket) -> None:
    global input_text
    global is_running
    while is_running:
        data = s.recv(1024)
        if not data:
            break
        recieved = data.decode()
        delimiter, message = recieved.split(":", 1)
        nickname = message[:int(delimiter)]
        message = message[int(delimiter):]
        if nickname == "server" and message == "SHUTDOWN":
            print("\nSERVER SHUTTED DOWN")
            is_running = False
            break
        print("\r" + " " * (len(input_text) + len(my_nickname) + 10), end="")
        print(f"\r{nickname} - {message}")
        print(f"{my_nickname}(you) - {input_text}", end="")
        sys.stdout.flush()


def keep_alive():
    global is_running
    while is_running:
        message = my_nickname + "keepalive:"
        message = str(len(my_nickname)) + ":" + message
        s.sendall(message.encode())
        time.sleep(KEEP_ALIVE_DELAY)


while True:
    my_nickname = input("Enter your nickname - ")
    if my_nickname == "server" or my_nickname == "system":
        print("'server' and 'system' are reserved system names")
    else:
        break


print(f"""Hello, {my_nickname}. Connecting to server...
For exit type 'quit:'
To see online list, type 'online:'""")
s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.connect((HOST, PORT))

message = "system" + my_nickname
message = str(len("system")) + ":" + message
s.sendall(message.encode())

send_thread = threading.Thread(target=send_message, args=(s,), daemon=True)
keep_alive_thread = threading.Thread(target=keep_alive, daemon=True)
recv_thread = threading.Thread(target=receive_message, args=(s,), daemon=True)

send_thread.start()
recv_thread.start()
keep_alive_thread.start()

recv_thread.join()
s.close()
