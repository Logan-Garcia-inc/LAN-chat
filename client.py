import socket
import os
import time
import threading
import urllib.request
path=__file__
source="https://raw.githubusercontent.com/Logan-Garcia-inc/LAN-chat/sockets/client.py"
#with urllib.request.urlopen(source) as url:
   # code=url.read().decode("utf-8")
   # with open(path, "r") as file:
       # if (file.read() != code):
         #   if (input("update code? y/n :").lower()=="y"):
             #   with open(path, "w") as file:
             #       file.write(code)
            #        print("Updated code. Please restart.")
            #        time.sleep(5)
             #       quit()

def receive_from_server(s):
    while True:
        data = s.recv(1024).decode()
        if data:
            print(data)

def send_to_server(s):
    while True:
        message = input("Enter message to send: ")
        s.sendall(message.encode())

HOST = '127.0.0.1'
PORT = 42069

with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
    while True:
        try:
            print("Searching for host on " + HOST)
            s.connect((HOST, PORT))
            print("connected")
            break
        except ConnectionRefusedError:
            print("Connection refused")
    threading.Thread(target=send_to_server, args=(s,)).start()
    receive_from_server(s)
