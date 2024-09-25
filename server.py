import socket
import json
import os
import time
import threading
import urllib.request
path=__file__
lock= threading.Lock()
prod=True
if not prod:
    source="https://raw.githubusercontent.com/Logan-Garcia-inc/LAN-chat/main/server.py"
    with urllib.request.urlopen(source) as url:
        code=url.read().decode("utf-8")
        with open(path, "r") as file:
            if (file.read() != code):
                if (input("update code? y/n :").lower()=="y"):
                    with open(path, "w") as file:
                        file.write(code)
                        print("Updated code. Please restart.")
                        time.sleep(5)
                        quit()
lobbies={"default":{}}
def add_to_lobby(addr, conn,lobby):
    with lock:
        if lobby in lobbies:
           lobbies[lobby][addr]=conn
           return True
        else:
           lobbies[lobby]={}
           lobbies[lobby][addr]=conn
           return True
    
def remove_from_lobby(addr, lobby):
    with lock:
        lobbies[lobby].pop(addr)
        if len(lobbies[lobby])==0 and len(lobbies.keys())>1:
            lobbies.pop(lobby)

def handle_client(conn, addr):
    global lobbies
    name=""
    lobby=""
    send_to_client(conn,{"type":"query", "data":"lobby", "message":"Available lobbies:\n\n"+",".join(lobbies.keys())+"\n\nJoin or create lobby: "})
    while True:
        try:
            data = conn.recv(1024)
            data=data.decode("utf-8")
        except e:
            print(e)
        if not data:
            if lobby:
                remove_from_lobby(addr,lobby)
                send_to_clients(lobby, addr, {"type":"announcement", "message":name+" left"})
            conn.close()
            break
        print("Receiving: "+data)
        data=json.loads(data)
       
        if(data["type"]=="response"):
            if(data["data"]=="lobby"):
                name=data["name"]
                lobby=data["message"]
                if add_to_lobby(addr,conn,lobby):
                    send_to_client(conn,  {"type": "response", "data":"lobby", "message":"Joined: "+lobby})
                    send_to_clients(lobby,addr,{"type":"announcement", "message":name+" Joined"})
        if data["type"]=="message" and data["message"]:
            send_to_clients(lobby, addr, {"type":"message","message":data["message"], "from":data["name"]})
        
def send_to_clients(lobby,addr,  message):
     message = json.dumps(message)
     print("sending: "+message)
     for i in lobbies[lobby].keys():
        #print(addr)
        #print(i)
        if(addr!=i):
           lobbies[lobby][i].sendall(message.encode("utf-8"))

def send_to_client(conn, message):
    message = json.dumps(message)
    print("sending: "+message)
    conn.sendall(message.encode("utf-8"))

HOST = '0.0.0.0'
PORT = 42069

with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    s.bind((HOST, PORT))
    s.listen(5)
    print(f"Server listening on {HOST}:{PORT}...")
    while True:
        conn, addr = s.accept()
        print("Connected to "+str(addr)) #threading.Thread(target=send_to_client, args=(conn,addr)).start()
        threading.Thread(target=handle_client, args=(conn, addr)).start()
    s.close()
