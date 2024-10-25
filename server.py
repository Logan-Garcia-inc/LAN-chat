import os
try:
    import psutil
except ImportError:
    os.system("pip install psutil")
    import psutil
import socket
import json
import time
import threading
import urllib.request
import time
path=__file__
lock= threading.Lock()
prod=True
HOST = '0.0.0.0'
PORT = 42069
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
def getLanIp(interface_name='wlan0'):
    interfaces = psutil.net_if_addrs()
    if interface_name in interfaces:
        for snic in interfaces[interface_name]:
            if snic.family == socket.AF_INET:  # Look for the IPv4 address
                return snic.address
    return None
def broadcast():
    sock= socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEPORT, 1)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
    message=getLanIp().encode("utf-8")
    while True:
        sock.sendto(message, ('<broadcast>', PORT))
        print(message)
        time.sleep(1)
class Lobby:
    def __init__(self,name,password):
        self.name=name
        self.password=password
        self.users={}

class User:
    def __init__(self, conn, addr):
        self.password=""
        self.name=""
        self.addr=addr
        self.conn=conn
        self.lobby=""
    def set_password(self, password):
        self.password=password
    def set_name(self,name):
        self.name=name
    def set_addr(self,addr):
        self.addr=addr
    def set_conn(self,conn):
        self.conn=conn
    def set_lobby(self,lobby):
        self.lobby=lobby

lobbies={"default":Lobby("default","")}
def add_to_lobby(user):
    password=user.password
    addr=user.addr
    lobby=user.lobby
    conn=user.conn
    with lock:
        if not (lobby in lobbies):
            print(f"creating {lobby} password: {password}")
            lobbies[lobby]=Lobby(lobby, password)

        if (password==lobbies[lobby].password):
            lobbies[lobby].users[addr]=conn
            print(f"{addr} joined {lobby} with password '{password}'")
            return True
    return False

def remove_from_lobby(user):
    addr=user.addr
    lobby=user.lobby
    with lock:
        print(f"removing {addr} from {lobbies[lobby].users.keys()} ")
        lobbies[lobby].users.pop(addr)
        if len(lobbies[lobby].users.keys())==0 and lobby!="default":
            lobbies.pop(lobby)

def query_to_join_server(user, passwordFail=False):
    send_to_client(user,{"type":"query", "data":json.dumps({name: bool(lobby.password) for name, lobby in lobbies.items()}), "message":f"{'Incorrect password' if passwordFail else ''}Available lobbies:\n\n"+"\\"+"\n\nJoin or create lobby: "})

def handle_lobby_response(user,socket):
    if add_to_lobby(user):
        send_to_client(conn,  {"type": "response", "data":"lobby", "message":"Joined: "+lobby})
        send_to_clients(user,{"type":"announcement", "message":name+" Joined"})
    else:
        send_to_client(user,{"type:":"response","data":"lobby", "message":"wrong password"})
        
def handle_client(conn, addr):
    global lobbies
    user=User(conn,addr)
    lobby=""
    query_to_join_server(user)
    while True:
        data=""
        try:
            data = conn.recv(1024)
            data=data.decode("utf-8")
        except Exception as e:
            print(e)
      
        if not data:
            if user.lobby:
                remove_from_lobby(user)
                send_to_clients(user, {"type":"announcement", "message":user.name+" left"})
            conn.close()
            break
        #print("Receiving: "+data)
        data=json.loads(data)
       
        if(data["type"]=="response"):
            if(data["data"]=="lobby"):
                user.set_name(data["name"])
                user.lobby=data["message"]
                user.password=data["password"]
                if add_to_lobby(user):
                    send_to_client(user,  {"type": "response", "data":"lobby", "message":"Joined: "+lobby})
                    send_to_clients(user,{"type":"announcement", "message":user.name+" Joined"})
                else:
                    user.lobby=""
                    query_to_join_server(user,passwordFail=True)
        if data["type"]=="message" and data["message"]:
            send_to_clients(user, {"type":"message","message":data["message"], "from":data["name"]})
        
def send_to_clients(user,  message):
     lobby=user.lobby
     addr=user.addr
     message = json.dumps(message)
     for i in lobbies[lobby].users.keys():
        if(addr!=i):
           lobbies[lobby].users[i].sendall(message.encode("utf-8"))

def send_to_client(user, message):
    message = json.dumps(message)
    print("sending: "+message)
    user.conn.sendall(message.encode("utf-8"))

with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    s.bind((HOST, PORT))
    s.listen(10)
    print(f"Server listening on {HOST}:{PORT}...")
    threading.Thread(target=broadcast,args=()).start()
    while True:
        conn, addr = s.accept()
        conn.settimeout(60)
        print(addr)
        print("Connected to "+str(addr)) #threading.Thread(target=send_to_client, args=(conn,addr)).start()
        threading.Thread(target=handle_client, args=(conn, addr)).start()
    s.close()
