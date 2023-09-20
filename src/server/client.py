import struct

YELLOW = lambda x: "\033[93m" + x + "\033[0m"  # for nice terminal printing


class Client:
    def __init__(self, connection, address, name, parent):
        self.conn = connection
        self.addr = address
        self.name = name
        self.room = None
        self.parent = parent

    def send_msg(self, msg):
        # send a message
        raw_msg = msg.encode()
        try:
            self.conn.sendall(struct.pack(">I", len(raw_msg)) + raw_msg)
        except:
            self.parent.remove_client(self)

    def recv_msg(self):
        # receive a message
        raw_msg_length = self.conn.recv(4)
        if not raw_msg_length:
            return None
        msg_length = struct.unpack(">I", raw_msg_length)[0]
        raw_msg = self.recv_amount(msg_length)
        if raw_msg is None:
            return None
        return raw_msg.decode()

    def recv_amount(self, n):
        # receive exactly n bytes
        data = bytearray()
        while len(data) < n:
            packet = self.conn.recv(n - len(data))
            if not packet:
                return None
            data.extend(packet)
        return data

    def recv_thread(self):
        # receive messages from this client
        while True:
            try:
                msg = self.recv_msg()  # self.conn.recv(2048).decode()
                print("{}: {}".format(YELLOW(self.name), msg))
                if msg == "state_request":
                    self.send_msg(self.room.current_status())
                elif msg == "bye":
                    self.send_msg("bye")
                    break
                elif msg is None:
                    break
                else:
                    self.room.handle_msg(msg, self)
            except:
                break
        self.parent.remove_client(self)
