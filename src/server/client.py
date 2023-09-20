YELLOW = lambda x: "\033[93m" + x + "\033[0m"  # for nice terminal printing


class Client:
    def __init__(self, connection, address, name, parent):
        self.conn = connection
        self.addr = address
        self.name = name
        self.room = None
        self.parent = parent

    def send(self, msg):
        # send a message to this client
        try:
            self.conn.send(msg.encode())
        except:
            self.parent.remove_client(self)

    def recv_thread(self):
        # receive messages from this client
        while True:
            try:
                msg = self.conn.recv(2048).decode()
                print("{}: {}".format(YELLOW(self.name), msg))
                if msg == "state_request":
                    self.send(self.room.current_status())
                elif msg == "bye":
                    self.send("bye")
                    break
                elif not msg:
                    break
                else:
                    self.room.handle_msg(msg, self)
            except:
                break
        self.parent.remove_client(self)
