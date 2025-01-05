import os
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
                        print(code)
                        file.write(code)
                        print("Updated code. Please restart.")
                        time.sleep(5)
                        quit()
                else:
                    print("Running old version")
def getLanIp():
    interfaces = psutil.net_if_addrs()
    stats = psutil.net_if_stats()
    for interface_name, snics in interfaces.items():
        if interface_name in stats and stats[interface_name].isup:
            print(interface_name)
            for snic in snics:
                if snic.family == socket.AF_INET:
                    return snic.address
def broadcast():
    try:
        sock= socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        message=getLanIp().encode("utf-8")
        while True:
            sock.sendto(message, ('<broadcast>', PORT))
            print(message)
            time.sleep(1)
    except OSError as e:
        print("UDP broadcast failed. Server will not be discoverable.")
        print(e)
class Lobby:
    def __init__(self,name,password):
        self.name=name
        self.password=password
        self.users={}

class User:
    uniqueID=1
    def __init__(self, conn, addr):
        self.password=""
        self.name=""
        self.addr=addr
        self.conn=conn
        self.lobby=""
        self.id=User.uniqueID
        User.uniqueID+=1

lobbies={"default":Lobby("default","")}
def add_to_lobby(user):
    password=user.password
    id=user.id
    lobby=user.lobby
    conn=user.conn
    if not lobby:
        return False
    with lock:
        if not (lobby in lobbies):
            print(f"creating {lobby} password: {password}")
            lobbies[lobby]=Lobby(lobby, password)

        if (password==lobbies[lobby].password):
            lobbies[lobby].users[id]=conn
            print(f"{id} joined {lobby} with password '{password}'")
            return True
    return False

def remove_from_lobby(user):
    id=user.id
    lobby=user.lobby
    with lock:
        print(f"removing {id} from {lobbies[lobby].users.keys()} ")
        lobbies[lobby].users.pop(id)
        if len(lobbies[lobby].users.keys())==0 and lobby!="default":
            lobbies.pop(lobby)

def getInfo(user):
    send_to_client(user, {"type":"query","data":"info"})
    
def query_to_join_server(user, passwordFail=False):
    send_to_client(user,{"type":"query",
                         "data":"lobby",
"lobbies":"",
                         "message":('Incorrect password\n' if passwordFail else '')+
                                "Available lobbies:\n\n"+ "//"+
                                 "\n\nJoin or create lobby: "
                                })
   

def handle_lobby_response(user):
    if add_to_lobby(user):
        send_to_client(user,  {"type": "response", "data":"lobby", "message":"Joined: "+user.lobby})
        send_to_clients(user,{"type":"announcement", "message":user.name+" Joined"})
    else:
        user.lobby=""
        query_to_join_server(user,passwordFail=True)
        
def handle_client(conn, addr):
    global lobbies
    user=User(conn,addr)
    while True:
        if(user.name and not user.lobby):
            query_to_join_server(user)
        else:
            getInfo(user)
        data=""
        try:
            data = conn.recv(1024)
            data=data.decode("utf-8")
        except Exception as e:
            print(e)
        if not data:
            if user.lobby:
                send_to_clients(user, {"type":"announcement", "message":user.name+" left"})
                remove_from_lobby(user)
            conn.close()
            break
        #print("Receiving: "+data)
        data=json.loads(data)
        user.password=data["password"]
        if(data["type"]=="response"):
            if data["data"]=="info":
                user.name=data["name"]
            if(data["data"]=="lobby"):
                user.lobby=data["message"]
                handle_lobby_response(user)
        if data["type"]=="message" and data["message"]:
            send_to_clients(user, {"type":"message","message":data["message"], "from":data["name"]})
       
def send_to_clients(user,  message):
     lobby=user.lobby
     id=user.id
     message = json.dumps(message)
     for i in lobbies[lobby].users.keys():
        if(id!=i):
           lobbies[lobby].users[i].sendall(message.encode("utf-8"))

def send_to_client(user, message):
    message = json.dumps(message)
    print("sending: "+message)
    user.conn.sendall(message.encode("utf-8"))

HOST = '0.0.0.0'
PORT = 42069
try:
    import psutil
except ImportError:
    os.system("pip install psutil")
    import psutil
with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    s.bind((HOST, PORT))
    s.listen(10)
    print(f"Server listening on {HOST}:{PORT}...")
    threading.Thread(target=broadcast,args=()).start()
    while True:
        conn, addr = s.accept()
        conn.settimeout(60)
        print("Connected to "+str(addr)) #threading.Thread(target=send_to_client, args=(conn,addr)).start()
        threading.Thread(target=handle_client, args=(conn, addr)).start()
    s.close()
