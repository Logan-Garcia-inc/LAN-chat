name="bob"
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
s=""
should_exit = False
password=""
lobby=""
secret=""
path=__file__
PORT=42069
# if not debug:
#     source="https://raw.githubusercontent.com/Logan-Garcia-inc/LAN-chat/main/client.py"
#     with urllib.request.urlopen(source) as url:
#         code= "\n".join(url.read().decode("utf-8").split("\n")[2:])
#         with open(path, "r") as file:
#             localCode="".join(file.readlines()[2:])
#             if ( localCode != code):
#                 if (input("update code? y/n: ").lower()=="y"):
#                     with open(path+".temp", "w") as file:
#                         file.write(code)
#                         os.remove(path)
#                         os.rename(path+".temp",path)
#                         print("Updated code. Please restart.")
#                         time.sleep(5)
#                         quit()
def debug_print(*args,**kwargs):
    if debug:
        print(*args,**kwargs)
def checkCommands(val):
    if not val:
        return
    command, *args=val.split()
    result="Command not known"
    try:
        match command:
            case "quit":
                global should_exit
                should_exit=True
                s.close()
                result="Left "+lobby
                main()
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
    while not should_exit:
        print("Enter message to send: \n")
        send_to_server(s)

def get_lobbies(s):
    send_to_server(s,type="query", data="lobby")
def get_secret(s):
     send_to_server(s,type="query", data="secret")

def receive_from_server(s):
    global secret
    while not should_exit:
        try:
            data = s.recv(1024)
        except ConnectionResetError as e:
            s.close()
            break
        debug_print("receiving: ",end="" )
        debug_print(data) 
        if not data:
            print("Server disconnected")
            s.close()

        if secret:
            debug_print(data)
            data=secret.decrypt(data)
        else:
            data=data.decode("utf-8")

        data=json.loads(data)
        debug_print(data)
        handleResponse(s,data)

def handleResponse(s,data):
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
                get_lobbies(s)
        if data["data"]=="lobbyList":
            lobbyJoin(data)
        if data["data"]=="secret":
            secret=Fernet(data["message"].encode())
        
    if data["type"]=="query":
        print(data)
        if data["data"]=="info":
            send_to_server(s, type="response", data="info")

def send_to_server(s, type="message", data="", message=""):
        if not message and type=="message":
            message = input()
            checkCommands(message)
#        debug_print("sending: "+message)
        data =json.dumps({"type":type,"data":data,"message":message,"name":name,"password":password})
        if not should_exit:
            if secret:
                data=secret.encrypt(data.encode())
                s.sendall(data)
            else:
                s.sendall(data.encode("utf-8"))
def main():
    global HOST
    global s
    global secret
    global should_exit
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
            should_exit=False
            receive_from_server(s)
        except ConnectionRefusedError:
            print("Connection refused")
main()