debug=True
import os
import socket
import json
import time
import threading
import urllib.request
try:
    from cryptography.fernet import Fernet
except ImportError:
    os.system("pip install cryptography")
    from cryptography.fernet import Fernet
path=__file__
lock= threading.Lock()
HOST = '0.0.0.0'
PORT = 42069
# if not debug:
#     source="https://raw.githubusercontent.com/Logan-Garcia-inc/LAN-chat/main/server.py"
#     with urllib.request.urlopen(source) as url:
#         code=url.read().decode("utf-8")
#         with open(path, "r") as file:
#             if (file.read() != code):
#                 if (input("update code? y/n: ").lower()=="y"):
#                     with open(path+".temp", "w") as file:
#                         file.write(code)
#                         os.remove(path)
#                         os.rename(path+".temp",path)
#                         print("Updated code. Please restart.")
#                         time.sleep(3)
#                         quit()
#                 else:
#                     print("Running old version")
def debug_print(*args ,**kwargs):
    if debug:
        print(*args,**kwargs)
def getLanIp():
    """
    Get the local LAN IPv4 address of the machine.
    Returns:
    str: The LAN IP address.
    """
    try:
            # Create a socket connection to an external server to determine the local IP
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
                # Doesn't need to actually connect, just triggers local IP resolution
            s.connect(("8.8.8.8", 80))
            return s.getsockname()[0]
    except Exception as e:
        raise RuntimeError(f"Unable to determine LAN IP: {e}")

def broadcast():
    try:
        sock= socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        message=getLanIp().encode("utf-8")
        while True:
            sock.sendto(message, ('<broadcast>', PORT))
            #print(message)
            time.sleep(1)
    except OSError as e:
        print("UDP broadcast failed. Server will not be discoverable.")
        debug_print("error cause: ", end="")
        debug_print(e)

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
        self.secret="" 

lobbies={"default":Lobby("default","")}
def add_to_lobby(user,lobby):
    password=user.password
    id=user.id
    conn=user.conn
    if not lobby:
        return False
    with lock:
        if not (lobby in lobbies):
            #print(f"creating {lobby} password: {password}")
            lobbies[lobby]=Lobby(lobby, password)

        if (password==lobbies[lobby].password):
            lobbies[lobby].users[id]=user
            #print(f"{id} joined {lobby} with password '{password}'")
            return True
    return False

def remove_from_lobby(user):
    id=user.id
    lobby=user.lobby
    with lock:
       # print(f"removing {id} from {lobbies[lobby].users.keys()} ")
        lobbies[lobby].users.pop(id)
        if len(lobbies[lobby].users.keys())==0 and lobby!="default":
            lobbies.pop(lobby)

def getInfo(user):
    send_to_client(user, {"type":"query","data":"info"})
    
def handle_lobby_query(user, passwordFail=False):
    send_to_client(user,{"type":"response",
                         "data":"lobbyList",
"lobbies": [
    [lobby.name, bool(lobby.password), len(lobby.users)]
    for lobby in lobbies.values()
],
                         "message":('Incorrect password\n' if passwordFail else '')+
                                "Available lobbies:\n\n"+ "//"+
                                 "\n\nJoin or create lobby: "
                                })
   

def handle_lobby_response(user,lobby):
    if add_to_lobby(user,lobby):
        user.lobby=lobby
        send_to_client(user,  {"type": "response", "data":"lobbyJoin", "message":"Joined: "+user.lobby})
        send_to_clients(user,{"type":"announcement", "message":user.name+" Joined"})
    else:
        send_to_client(user,{"type": "response", "data":"lobbyJoin", "message":"fail"})
#        query_to_join_server(user,passwordFail=True)
        
def handle_client(conn, addr):
    global lobbies
    user=User(conn,addr)
    while True:
        data=""
        try:
            data = conn.recv(1024)
        except Exception as e:
            print(e)
        if not data:
            if user.lobby:
                send_to_clients(user, {"type":"announcement", "message":user.name+" left"})
                remove_from_lobby(user)
            conn.close()
            break
        debug_print("Receiving: ", end="")
        debug_print(data)
        try:
            data=user.secret.decrypt(data).decode()
        except Exception as e:
            #print (e)
            data=data.decode("utf-8")
        debug_print("decoded: "+data)
        data=json.loads(data)
        user.password=data["password"]
        if data["name"]:
            user.name=data["name"]
        if(data["type"]=="response"):
            if data["data"]=="info":
                user.name=data["name"]
            if data["data"]=="lobby":
                handle_lobby_response(user,data["message"])
        if data["type"]=="message" and data["message"]:
            send_to_clients(user, {"type":"message","message":data["message"], "from":data["name"]})
        if data["type"]=="query":
            if data["data"]=="lobby":
                handle_lobby_query(user, data["message"])
            if data["data"]=="secret":
                key =Fernet.generate_key()
                send_to_client(user, {"type":"response","data":"secret","message":key.decode("utf-8")})
                user.secret=Fernet(key)
        debug_print("\n")
def send_to_clients(user,  message):
     lobby=user.lobby
     id=user.id
     for user in lobbies[lobby].users.keys():
        if(id!=user):
           send_to_client(lobbies[lobby].users[user],message)

def send_to_client(user, message):
    message = json.dumps(message)
    debug_print("sending: "+message)
    if user.secret !="":
        message=user.secret.encrypt(message.encode())
        user.conn.sendall(message)
    else:
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
