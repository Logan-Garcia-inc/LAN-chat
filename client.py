name=""
HOST=""
import json
import socket
import os
import time
import threading
import urllib.request
password=""
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
                    with open(path, "w") as file:
                        file.write(code)
                        print("Updated code. Please restart.")
                        time.sleep(5)
                        quit()
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
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEPORT, 1)
    sock.bind(("",42069))
    print("searching")
    data=sock.recv(1024).decode("utf-8")
    print(data)
    HOST=data
    sock.close()

#    with open(path, "r") as file:
 #       lines=file.readlines()
  #  lines[1]='HOST="'+HOST+'"\n'
   # with open(path, "w") as file:
    #    file.writelines(lines)
def send_loop(s):
    print("Enter message to send: \n")
    while True:
        send_to_server(s)
def receive_from_server(s):
    global password
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
        try:
            data=json.loads(data.decode("utf-8"))
        except JSONDecodeError:
            print("JSON decode error: "+data)
def handleResponse():
    if data["type"]=="message":
        print(data["from"]+": "+data["message"])
    if data["type"]=="announcement":
        print(data["message"])
    if data["type"]=="response":
        if data["data"]=="lobby":
            if data["message"].split(":")[0]=="Joined":
                print(data["message"])
                threading.Thread(target=send_loop, args=(s,)).start()
    if data["type"]=="query":
        message=""
        lobbies = json.loads(data["data"])
        for name, is_protected in lobbies.items():
            lock_symbol = "\U0001f512" if is_protected else ""
            message += f"{name} {lock_symbol}\n"
        #filter message?? lobby =input(data["message"].replace("\\",message))
        if(lobby in lobbies):
            if (lobbies[lobby]):
                password=input("password: ") 
        else:
            password=input("Set password: ")
        send_to_server(s,"response","lobby",lobby)

def send_to_server(s, type="message", data="", message=""):
        if not message:
            message = input()
#        print("sending: "+message)
        s.sendall(json.dumps({"type":type,"data":data,"message":message,"name":name,"password":password}).encode("utf-8"))

with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
    try:
        print("Searching for host")
        findServer()
        s.connect((HOST, PORT))
        print("connected\n")
        receive_from_server(s)
    except ConnectionRefusedError:
        print("Connection refused")
