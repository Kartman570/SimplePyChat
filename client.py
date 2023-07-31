import socket
import time
import threading
import sys

HOST = "127.0.0.1"
PORT = 12345
KEEP_ALIVE_DELAY = 1
IS_RUNNING = True

my_nickname = ""
input_text = ""

def send_message(s: socket.socket) -> None:
    global input_text
    while True:
        input_text = input(f"{my_nickname}(you) - ")
        s.sendall((my_nickname + ":" + input_text).encode())
        if input_text == "quit:":
            IS_RUNNING = False
            break

def receive_message(s: socket.socket) -> None:
    global input_text
    global IS_RUNNING
    while IS_RUNNING:
        data = s.recv(1024)
        if not data:
            break
        message = data.decode()
        nickname, message = message.split(":", 1)
        if nickname == "server" and message == "SHUTDOWN":
            print("\nSERVER SHUTTED DOWN")
            IS_RUNNING = False
            break
        print("\r" + " " * (len(input_text) + len(my_nickname) + 10), end="")
        print(f"\r{nickname} - {message}")
        print(f"{my_nickname}(you) - {input_text}", end="")
        sys.stdout.flush()
        

def keep_alive():
    global IS_RUNNING
    while IS_RUNNING:
        s.sendall((my_nickname + ":keepalive:").encode())
        time.sleep(KEEP_ALIVE_DELAY)


while True:
    my_nickname = input("Enter your nickname - ")
    if ":" in my_nickname:
        print("char ':' not alowed for username")
    elif my_nickname == "server":
        print("'server' is reserved system name")
    else:
        break

print(f"\nHello, {my_nickname}. Connecting to server...\nFor exit type 'quit:'\nTo see online list, type 'online:'\n")
s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.connect((HOST, PORT))
s.sendall(str(my_nickname + ":new_user:").encode())

send_thread = threading.Thread(target=send_message, args=(s,), daemon=True)
keep_alive_thread = threading.Thread(target=keep_alive, daemon=True)
recv_thread = threading.Thread(target=receive_message, args=(s,), daemon=True)

send_thread.start()
recv_thread.start()
keep_alive_thread.start()

recv_thread.join()
s.close()

