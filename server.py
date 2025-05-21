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
from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.hazmat.primitives import serialization, hashes
from cryptography.hazmat.primitives.kdf.hkdf import HKDF
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
path=__file__
lock= threading.Lock()
HOST = '0.0.0.0'
PORT = 42069
private_key = ec.generate_private_key(ec.SECP256R1())
public_key = private_key.public_key()

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
    
def encrypt(plaintext, aes_key):
    vector=os.urandom(12)
    encryptor = Cipher(algorithms.AES(aes_key),modes.GCM(vector)).encryptor()
    encryptedText=vector+encryptor.update(plaintext)+encryptor.tag()
    return encryptedText

def decrypt(data, aes_key):
    vector = data[:12]  
    text = data[12:-16]  
    tag = data[-16:]
    decryptor = Cipher(algorithms.AES(aes_key),modes.GCM(vector, tag)).decryptor()
    decrypted_data = decryptor.update(text) + decryptor.finalize()
    return decrypted_data

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
        self.aes_key=None

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
    send_to_clients(user, {"type":"announcement", "message":user.name+" left"})
    with lock:
       # debug_print(f"removing {id} from {lobbies[lobby].users.keys()} ")
        lobbies[lobby].users.pop(id)
        if len(lobbies[lobby].users.keys())==0 and lobby!="default":
            lobbies.pop(lobby)
        user.lobby=""

def createSymmetricKey(pub,priv):
    derived_key=priv.exchange(ec.ECDH(), pub)
    aes_key=HKDF(algorithm=hashes.SHA256(),length=32, salt=None, info=b'key exchange').derive(derived_key)
    return aes_key

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
                remove_from_lobby(user)
            conn.close()
            break
        debug_print("Receiving: ", end="")
        debug_print(data)
        try:
            data=data.decode("utf-8")
        except Exception as e:
            #print (e)
            data=decrypt(data, user.aes_key)
        debug_print("decoded: "+data)
        data=json.loads(data)
        user.password=data["password"]
        if data["name"]:
            user.name=data["name"]
        
        if(data["type"]=="response"):                                   #responses
            if data["data"]=="info":
                user.name=data["name"]
            if data["data"]=="lobby":
                handle_lobby_response(user,data["message"])
            if data["data"]=="secret":
                print(data["message"])
                user.aes_key=createSymmetricKey(serialization.load_pem_public_key(data["message"].encode("utf-8")), private_key)
                print(user.aes_key)

        if data["type"]=="message" and data["message"]:              #messages
            send_to_clients(user, {"type":"message","message":data["message"], "from":data["name"]})

        if data["type"]=="query":                                    #queries
            match(data["data"]):
                case "lobby":
                    handle_lobby_query(user, data["message"])
                case "secret":
                    key = public_key.public_bytes(encoding=serialization.Encoding.PEM,format=serialization.PublicFormat.SubjectPublicKeyInfo)
                    send_to_client(user, {"type":"response","data":"secret","message":key.decode("utf-8")},encrypted=False)
                    threading.Event().wait(0.2)
                case "quitLobby":
                    remove_from_lobby(user)
                    handle_lobby_query(user)
        debug_print("\n")
        if user.aes_key==None:
            send_to_client(user, {"type":"query","data":"secret"})


def send_to_clients(user,  message):
     lobby=user.lobby
     id=user.id
     if not lobby:
        return
     for user in lobbies[lobby].users.keys():
        if(id!=user):
           send_to_client(lobbies[lobby].users[user],message)

def send_to_client(user: User, message,encrypted=True):
    message = json.dumps(message)
    debug_print("sending: "+message)
    if user.aes_key !=None and encrypted:
        message=encrypt(message.encode(),user.aes_key)
        user.conn.sendall(message)
    else:
        user.conn.sendall(message.encode("utf-8"))

HOST = '0.0.0.0'
PORT = 42069
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
