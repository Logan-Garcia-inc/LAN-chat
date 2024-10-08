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
                else:
                    print("Running old version")
class Lobby:
    def __init__(self,name,password):
        self.name=name
        self.password=password
        self.users={}#users{("127.0.0.1", 23456), socket}
        
lobbies={"default":Lobby("default","")}
def add_to_lobby(addr, conn,lobby, password):
    with lock:
#delete line        print("'"+lobbies[lobby].password+"' '"+password+"'")
        if lobby in lobbies:
            print("'"+lobbies[lobby].password+"' '"+password+"'")
            if (password==lobbies[lobby].password):
                
                lobbies[lobby].users[addr]=conn
                
            else:
                return False
        else:
            lobbies[lobby]=Lobby(lobby, password)
    return True

    
def remove_from_lobby(addr, lobby):
    with lock:
        lobbies[lobby].users.pop(addr)
        if len(lobbies[lobby].users)==0 and len(lobbies.keys())>1:
            lobbies.pop(lobby)

def handle_lobby_response(name,lobby,password,addr,socket):
    if add_to_lobby(addr,conn,lobby, password):
        send_to_client(conn,  {"type": "response", "data":"lobby", "message":"Joined: "+lobby})
        send_to_clients(lobby,addr,{"type":"announcement", "message":name+" Joined"})
    else:
        send_to_client(conn,{"type:":"response","data":"lobby", "message":"wrong password"})
        
def handle_client(conn, addr):
    global lobbies
    name=""
    lobby=""
    send_to_client(conn,{"type":"query", "data":json.dumps({name: bool(lobby.password) for name, lobby in lobbies.items()}), "message":"Available lobbies:\n\n"+"\\"+"\n\nJoin or create lobby: "})
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
                password=data["password"]
                handle_lobby_response(name,lobby,password,addr,conn)
        if data["type"]=="message" and data["message"]:
            send_to_clients(lobby, addr, {"type":"message","message":data["message"], "from":data["name"]})
        
def send_to_clients(lobby,addr,  message):
     message = json.dumps(message)
     print("sending: "+message)
     print(lobbies[lobby].users.keys())
     for i in lobbies[lobby].users.keys():
        #print(addr)
        #print(i)
        if(addr!=i):
           lobbies[lobby].users[i].sendall(message.encode("utf-8"))

def send_to_client(conn, message):
    message = json.dumps(message)
    print("sending: "+message)
    conn.sendall(message.encode("utf-8"))

HOST = '0.0.0.0'
PORT = 42069

with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    s.bind((HOST, PORT))
    s.listen(10)
    print(f"Server listening on {HOST}:{PORT}...")
    while True:
        conn, addr = s.accept()
        print("Connected to "+str(addr)) #threading.Thread(target=send_to_client, args=(conn,addr)).start()
        threading.Thread(target=handle_client, args=(conn, addr)).start()
    s.close()
