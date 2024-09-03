name=""
import json
import socket
import os
import time
import threading
import urllib.request
path=__file__
source="https://raw.githubusercontent.com/Logan-Garcia-inc/LAN-chat/main/client.py"

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

if not name:
    name=input("Set name: ")
    with open(path, "r") as file:
        lines=file.readlines()
    lines[0]='name="'+name+'"'
    with open(path, "rw") as file:
        file.writelines(lines)
def send_loop(s):
    while True:
        send_to_server(s)

def receive_from_server(s):
    while True:
        data = json.loads(s.recv(1024).decode())
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
        if not  message:
            message = input("Enter message to send: ")
        s.sendall(json.dumps({"type":type,"data":data,"message":message,"name":name}).encode())

HOST = '127.0.0.1'
PORT = 42069

with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
    while True:
        try:
            print("Searching for host on " + HOST)
            s.connect((HOST, PORT))
            print("connected\n")
            break
        except ConnectionRefusedError:
            print("Connection refused")
    receive_from_server(s)
