import socket
import threading

def handle_client(conn, addr):
    while True:
        data = conn.recv(1024)
        if data:
            print("\n"+data.decode("utf-8")+"\nEnter message to send: ")

def send_to_client(conn):
    while True:
        message = input("Enter message to send: ")
        conn.sendall(message.encode("utf-8"))

HOST = '0.0.0.0'
PORT = 42069

with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
    s.bind((HOST, PORT))
    s.listen()
    print(f"Server listening on {HOST}:{PORT}...")
    conn, addr = s.accept()
    print("Connected to "+str(addr))
    threading.Thread(target=send_to_client, args=(conn,)).start()
    handle_client(conn, addr)
