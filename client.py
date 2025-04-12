name=""
HOST=""
debug=True
import json
import socket
import os
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
send_loop_thread=""
s=""
password=""
lobby=""
private_key = ec.generate_private_key(ec.SECP256R1())
public_key = private_key.public_key()
aes_key=""
path=__file__
PORT=42069

def debug_print(*args,**kwargs):
    if debug:
        print(*args,**kwargs)

def checkCommands(val):
    global send_loop_thread
    if not val:
        return
    command, *args=val.split()
    result="Command not known"
    try:
        match command:
            case "/quit":
                send_to_server(s, "query","quitLobby")
                print("Left "+lobby)
                result="quit"
            case "/help":
                print(
                    """
        /help:    Display command usage
        /quit:    Leave the current lobby""")
    except Exception as e:
        result="Command failed"
    return result

def askName():
    global name
    if not name:
        name=input("Set name: ")
        if not debug:
            with open(path, "r") as file:
                lines=file.readlines()
                lines[0]='name="'+name+'"\n'
            with open(path, "w") as file:
                file.writelines(lines)
def findServer():
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sock.bind(("",42069))
    serverIP=sock.recv(1024).decode("utf-8")
    sock.close()
    return serverIP

def lobbyJoin(data):
    global lobby
    global password 
    lobbyExists = False
    message=data["message"]
    lobbyChoice = input(message.replace("//","\n".join([(name+"\U0001f512 " if password else name+" ")+
                                 str(users)+
                                 "\U0001F464\n" for name,lobby,users in data["lobbies"]])))
    for lobby in data["lobbies"]:
        if lobby[0] == lobbyChoice:  # Check if lobby exists
            lobbyExists=True
            if lobby[1]:  # Check if password-protected
                password=input("password: ")
                break
    if not lobbyExists:
        password=input("set password (blank for none): ")
    lobby=lobbyChoice
    send_to_server(s,"response","lobby",lobby)

def send_loop(s):
        print("Enter message to send: \n")
        while True:
            message = input()
            if message[0]=="/":
                if checkCommands(message)=="quit":
                    return
            send_to_server(s, message=message)

def get_lobbies(s):
    send_to_server(s,type="query", data="lobby")

def get_secret(s):
     send_to_server(s,type="query", data="secret")

def encrypt(plaintext):
    global aes_key
    vector=os.urandom(12)
    encryptor = Cipher(algorithms.AES(aes_key),modes.GCM(vector)).encryptor()
    encryptedText=vector+encryptor.update(plaintext)+encryptor.tag()
    return encryptedText

def decrypt(message):
    vector = message[:12]  
    text = message[12:-16]  
    tag = message[-16:]
    decryptor = Cipher(algorithms.AES(aes_key),modes.GCM(vector, tag)).decryptor()
    decrypted_message = decryptor.update(text) + decryptor.finalize()
    return decrypted_message

def receive_from_server(s):
    global secret
    while True:
        try:
            data = s.recv(1024)
        except ConnectionResetError as e:
            s.close()
        debug_print("receiving: ",end="" )
        debug_print(data) 
        if not data:
            s.close()
        if secret:
            data=secret.decrypt(data)
        else:
            data=data.decode("utf-8")

        data=json.loads(data)
        handleResponse(s,data)

def handleResponse(s,data):
    global send_loop_thread
    global private_key
    global encryptor
    global aes_key
    match (data["type"]):
        case "message":
            print(data["from"]+": "+data["message"])
        case "announcement":
            print(data["message"])

        case "response":
            if data["data"]=="lobbyJoin":
                if data["message"].split(":")[0]=="Joined":
                    print(data["message"])
                    send_loop_thread = threading.Thread(target=send_loop, args=(s,))
                    send_loop_thread.start()
                else:
                    get_lobbies(s)
            if data["data"]=="lobbyList":
                lobbyJoin(data)
            if data["data"]=="secret":
                server_public_key=serialization.load_pem_public_key(data["message"])
                derived_key=private_key.exchange(ec.ECDH(), server_public_key)
                aes_key=HKDF(algorithm=hashes.SHA256(),length=32, salt=None info=b'key exchange').derive(derived_key)
               
            
        case "query":
            print(data)
            if data["data"]=="info":
                send_to_server(s, type="response", data="info")

def send_to_server(s=socket, type="message", data="", message=""):
        global secret
#        debug_print("sending: "+message)
        data =json.dumps({"type":type,"data":data,"message":message,"name":name,"password":password})
    
        if secret:
            data=secret.encrypt(data.encode())
            s.sendall(data)
        else:
            s.sendall(data.encode("utf-8"))
def main():
    global HOST
    global s
    global secret
    secret=""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        try:
            print("Searching for host")
            if not HOST:
                HOST = findServer()
            s.connect((HOST, PORT))
            askName()
            time.sleep(0.1)
            print("connected\n")
            get_secret(s)
            get_lobbies(s)
            receive_from_server(s)
        except ConnectionRefusedError:
            print("Connection refused")
main()