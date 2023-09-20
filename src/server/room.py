from datetime import datetime


class Room:
    def __init__(self, name, password, parent_server):
        self.name = name  # room name
        self.password = password  # room password
        self.parent = parent_server  # server object
        self.clients = []  # list of participating clients
        self.nclients = 0  # number of participants
        self.last_known_timestamp = 0  # last known timestamp of the media in ms
        self.last_timeupdate = None
        self.playing = False  # whether the media is currently playing

    def add_client(self, client):
        self.clients.append(client)
        self.nclients += 1
        client.room = self

    def remove_client(self, client):
        self.nclients -= 1
        self.clients.remove(client)
        self.broadcast("room_leave;;{} has left the room".format(client.name))
        if self.nclients == 0:
            self.parent.remove_room(self)

    def handle_msg(self, msg, sender):
        self.broadcast(msg, exception=sender)
        info = msg.split(";;")
        if info[0] == "pause":
            self.playing = False
            self.last_known_timestamp = info[1]
            self.last_timeupdate = datetime.now()
        elif info[0] == "play":
            if self.last_timeupdate is None:
                self.last_timeupdate = datetime.now()
            self.playing = True
        elif info[0] == "change_time":
            self.last_known_timestamp = int(info[1])
            self.last_timeupdate = datetime.now()

    def broadcast(self, msg, exception=None):
        # broadcast a message to all clients in this room
        self.parent.broadcast(msg, self.clients, exception)

    def timestamp(self):
        # return the current timestamp of the media in ms
        if not self.playing:
            return self.last_known_timestamp
        else:
            delta = datetime.now() - self.last_timeupdate
            ms_delta = delta.seconds * 1000 + round(delta.microseconds / 1000)
            return self.last_known_timestamp + ms_delta

    def current_status(self):
        state = "playing" if self.playing else "paused"
        return "{};;{}".format(state, self.timestamp())
