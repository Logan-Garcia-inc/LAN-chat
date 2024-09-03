import socket
import json
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
lobbies={}
def add_to_lobby(addr, conn,lobby):
     print(lobby+ " in "+ ",".join(lobbies.keys())+": "+ lobby in lobbies)

     if lobby in lobbies:
        lobbies[lobby][addr]=conn
        return True
     else:
        lobbies[lobby]={}
        lobbies[lobby][addr]=conn
        return True

def remove_from_lobby(addr, lobby):
    lobbies[lobby].pop(addr)
    if len(lobbies[lobby])==0:
        lobbies.pop(lobby)

def handle_client(conn, addr):
    global lobbies
    lobby=""
    send_to_client(conn,addr,{"type":"query", "data":"lobby", "message":"Available lobbies:\n\n"+",".join(lobbies.keys())+"\n\nJoin or create lobby: "})
    while True:
        data = conn.recv(1024).decode()
        if not data:
            if lobby:
                remove_from_lobby(addr,lobby)
            conn.close()
        data=json.loads(data)
        if(data["type"]=="response"):
            if(data["data"]=="lobby"):
                lobby= add_to_lobby(addr,conn,data["message"])
                    if lobby:
                        send_to_client(conn,addr,{"type": "response", "data":"lobby", "message":"joined:"+lobby})
        if data["type"]=="message":
            print(lobbies)
            for i in lobbies[lobby]:
                send_to_client(i[1], addr, {"type":"message","message":data["message"]})
        print(data)

def send_to_client(conn,addr, message):
    message = json.dumps(message)
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
        #threading.Thread(target=send_to_client, args=(conn,addr)).start()
        threading.Thread(target=handle_client, args=(conn, addr)).start()
    s.close()
