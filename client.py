name=""
HOST="127.0.0.1"
import json
import socket
import os
import time
import threading
import urllib.request
from cryptography.fernet import Fernet
password=""
lobby=""
secret=""
path=__file__
prod=True
PORT=42069
if not prod:
    source="https://raw.githubusercontent.com/Logan-Garcia-inc/LAN-chat/main/client.py"
    with urllib.request.urlopen(source) as url:
        code= "\n".join(url.read().decode("utf-8").split("\n")[2:])
        with open(path, "r") as file:
            localCode="".join(file.readlines()[2:])
            if ( localCode != code):
                if (input("update code? y/n :").lower()=="y"):
                    with open(path+".temp", "w") as file:
                        file.write(code)
                        os.remove(path)
                        os.rename(path+".temp",path)
                        print("Updated code. Please restart.")
                        time.sleep(5)
                        quit()
def askName():
    global name
    if not name:
        name=input("Set name: ")
        if not prod:
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
    message=data["message"]
    lobbyChoice = input(message.replace("//","\n".join([(name+"\U0001f512 " if password else name+" ")+
                                 str(users)+
                                 "\U0001F464\n" for name,lobby,users in data["lobbies"]])))
    for lobby in data["lobbies"]:
        if lobby[0] == lobbyChoice:  # Check if lobby exists
            if lobby[1]:  # Check if password-protected
                password=input("password: ")
                
        else:
            password=input("password (blank for none): ")
    lobby=lobbyChoice
    send_to_server(s,"response","lobby",lobby)
def send_loop(s):
    print("Enter message to send: \n")
    while True:
        send_to_server(s)

def get_lobbies(s):
    send_to_server(s,type="query", data="lobby")
def get_secret(s):
     send_to_server(s,type="query", data="secret")
def receive_from_server(s):
    global secret
    while True:
        try:
            data = s.recv(1024)
        except ConnectionResetError as e:
            s.close()
            break
        #print("receiving: "+ data)
        if not data:
            print("Server disconnected")
            s.close()
        if secret:
            data=secret.decrypt(data.decode())
        else:
            data=data.decode("utf-8")
        try:
            data=json.loads(data)
        except json.JSONDecodeError:
            print("JSON decode error: "+data)
        handleResponse(data)

def handleResponse(data):
    global secret
    if data["type"]=="message":
        print(data["from"]+": "+data["message"])
    if data["type"]=="announcement":
        print(data["message"])

    if data["type"]=="response":
        if data["data"]=="lobbyJoin":
            if data["message"].split(":")[0]=="Joined":
                print(data["message"])
                threading.Thread(target=send_loop, args=(s,)).start()
            else:
                get_lobbies()
        if data["data"]=="lobbyList":
            lobbyJoin(data)
        if data["data"]=="secret":
            secret=Fernet(data["message"].encode("utf-8"))
        
    if data["type"]=="query":
        print(data)
        if data["data"]=="info":
            send_to_server(s, type="response", data="info")

def send_to_server(s, type="message", data="", message=""):
        if not message and type=="message":
            message = input()
#        print("sending: "+message)
        data =json.dumps({"type":type,"data":data,"message":message,"name":name,"password":password})
        if secret:
            data=secret.encrypt(data.encode())
            s.sendall(data)
        else:
            s.sendall(data.encode("utf-8"))
with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
    try:
        print("Searching for host")
        if not HOST:
            HOST = findServer()
        s.connect((HOST, PORT))
        askName()
        print("connected\n")
        get_secret(s)
        get_lobbies(s)
        receive_from_server(s)
    except ConnectionRefusedError:
        print("Connection refused")
