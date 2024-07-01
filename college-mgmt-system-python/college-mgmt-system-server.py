# server.py
import socket
import threading
import sqlite3

HOST = '127.0.0.1'
PORT = 65432


def handle_client(conn):
    lock = threading.Lock()
    db_connection = sqlite3.connect('collegeMGMTsystem.db')
    cursor = db_connection.cursor()
    while True:
        data = conn.recv(1024).decode()
        if not data:
            break
        query = data.strip()
        try:
            with lock:
                cursor.execute(query)
                if query.lower().startswith('select'):
                    result = cursor.fetchall()
                    conn.sendall(str(result).encode())
                else:
                    conn.sendall(b'Success')
                db_connection.commit()
        except Exception as e:
            conn.sendall(str(e).encode())
    conn.close()


server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server_socket.bind((HOST, PORT))
server_socket.listen()
print(f"Server listening on {HOST}:{PORT}")
while True:
    conn, addr = server_socket.accept()
    print(f"Connected to {addr}")
    threading.Thread(target=handle_client, args=(conn,)).start()