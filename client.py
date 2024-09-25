name=""
HOST="127.0.0.1"
import json
import socket
import os
import time
import threading
import urllib.request
path=__file__
prod=True
if not prod:
    source="https://raw.githubusercontent.com/Logan-Garcia-inc/LAN-chat/main/client.py"
    with urllib.request.urlopen(source) as url:
        code= "\n".join(url.read().decode("utf-8").split("\n")[2:])
        with open(path, "r") as file:
            localCode="".join(file.readlines()[2:])
#            print(localCode)
            if ( localCode != code):
                if (input("update code? y/n :").lower()=="y"):
                    with open(path, "w") as file:
                        file.write(code)
                        print("Updated code. Please restart.")
                        time.sleep(5)
                        quit()
if not HOST:
    HOST=input("Set server IP: ")
    if prod:
        with open(path, "r") as file:
        
            lines=file.readlines()
        lines[1]='HOST="'+HOST+'"\n'
        with open(path, "w") as file:
            file.writelines(lines)

if not name:
    name=input("Set name: ")
    if not prod:
        with open(path, "r") as file:
            lines=file.readlines()
        lines[0]='name="'+name+'"\n'
        with open(path, "w") as file:
            file.writelines(lines)

def send_loop(s):
    print("Enter message to send: \n")
    while True:
        send_to_server(s)

def receive_from_server(s):
    while True:
        try:
            data = s.recv(1024).decode("utf-8")
            #print(data)
            
        except ConnectionResetError:
            break
        data=json.loads(data)
        if not data:
            s.close()
        #print(data)
        if data["type"]=="message":
            print(data["from"]+": "+data["message"])
        if data["type"]=="response":
            if data["data"]=="lobby":
                response=data["message"].split(":")
                if response[0]=="joined":
                    print("Joined: "+ response[1])
                    threading.Thread(target=send_loop, args=(s,)).start()
        if data["type"]=="query":
            if data["data"]=="lobby":
                lobby =input(data["message"])
                send_to_server(s,"response","lobby",lobby)

def send_to_server(s, type="message", data="", message=""):
        if not message:
            message = input()
        s.sendall(json.dumps({"type":type,"data":data,"message":message,"name":name}).encode())


PORT = 42069

with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
    try:
        print("Searching for host on " + HOST)
        s.connect((HOST, PORT))
        print("connected\n")
        receive_from_server(s)
    except ConnectionRefusedError:
        print("Connection refused")
    
