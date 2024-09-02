import socket
import os
import time
import threading
import urllib.request
path=__file__
source="https://raw.githubusercontent.com/Logan-Garcia-inc/LAN-chat/sockets/server.py"
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

def handle_client(conn, addr):
    while True:
        data = conn.recv(1024).decode()
        if not data:
            conn.close()
        print(data)

def send_to_client(conn,addr):
    message = input("Enter message to send: ")
    conn.sendall(message.encode())

HOST = '0.0.0.0'
PORT = 42069

with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
    s.bind((HOST, PORT))
    s.listen(5)
    print(f"Server listening on {HOST}:{PORT}...")
    while True:
        conn, addr = s.accept()
        print("Connected to "+str(addr))
        threading.Thread(target=send_to_client, args=(conn,addr)).start()
        threading.Thread(target=handle_client, args=(conn, addr)).start()
    s.close()
