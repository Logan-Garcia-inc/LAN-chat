import os
import threading
def client():
    os.system("python client.py")
def server():
    os.system("python server.py")
threading.Thread(target=client, args=()).start()
threading.Thread(target=server,args=()).start()
