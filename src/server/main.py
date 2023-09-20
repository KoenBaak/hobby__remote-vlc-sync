from socket import socket, AF_INET, SOCK_STREAM
import threading

# -------------------------------------------------------------------------------
from room import Room
from client import Client


IP = "localhost"
PORT = 6000
MAX_PART = 10  # maximum number of clients
YELLOW = lambda x: "\033[93m" + x + "\033[0m"  # for nice terminal printing
RED = lambda x: "\033[31m" + x + "\033[0m"
GREEN = lambda x: "\033[32m" + x + "\033[0m"



class MyServer:
    def __init__(self):
        self.sock = socket(AF_INET, SOCK_STREAM)
        self.sock.bind((IP, PORT))
        self.sock.listen(MAX_PART)

        self.nclients = 0  # number of connected clients
        self.nrooms = 0  # number of active rooms
        self.clients = []  # list of connected clients
        self.rooms = []  # list of active rooms
        self.accepting = False  # bool whether new clients are currently accepted

    def add_client(self, conn, addr):
        info = conn.recv(2048).decode().split(";;")  # wait for client info
        yellow_info = list(map(YELLOW, info))
        print(
            "connection received: {}, room: {}, given pw: {}, name: {}".format(
                *yellow_info
            )
        )
        if info[0] == "new":
            r = self.add_room(info[1], info[2])
        else:
            r = self.get_room_by_name(info[1])
            if not r:
                conn.send("Given room does not exist".encode())
                conn.close()
                print(
                    "Connection with {}".format(YELLOW(info[3])),
                    RED("rejected"),
                    "no valid room",
                )
                return
        if not info[2] == r.password:
            conn.send("Password incorrect".encode())
            conn.close()
            print(
                "Connection with {}".format(YELLOW(info[3])),
                RED("rejected"),
                "incorrect pw",
            )
            return
        new_client = Client(conn, addr, info[3], self)
        print("connection with {}".format(YELLOW(info[3])), GREEN("accepted"))
        self.clients.append(new_client)
        self.nclients += 1
        r.broadcast("room_enter;;{} has entered the room".format(new_client.name))
        r.add_client(new_client)
        resp = "succes;;" + ";;".join(c.name for c in r.clients)
        new_client.conn.sendall(resp.encode())
        threading.Thread(target=new_client.recv_thread).start()

    def accept(self):
        # accept new clients
        self.accepting = True
        while True:
            conn, addr = self.sock.accept()  # wait for connection
            self.add_client(conn, addr)
            if self.nclients == MAX_PART:
                self.accepting = False

    def get_room_by_name(self, name):
        for r in self.rooms:
            if r.name == name:
                return r
        return False

    def add_room(self, name, password):
        new_room = Room(name, password, self)
        self.nrooms += 1
        self.rooms.append(new_room)
        print("room added: ", YELLOW(name))
        return new_room

    def broadcast(self, msg, target_list, exception=None):
        # broadcast a message to all clients in target_list
        for c in target_list:
            if c != exception:
                c.send_msg(msg)

    def remove_client(self, client):
        client.room.remove_client(client)
        self.nclients -= 1
        self.clients.remove(client)
        client.conn.close()
        print("Removed client {}".format(YELLOW(client.name)))

    def remove_room(self, room):
        self.nrooms -= 1
        self.rooms.remove(room)
        print("room removed: ", YELLOW(room.name))


if __name__ == "__main__":
    s = MyServer()
    s.accept()
