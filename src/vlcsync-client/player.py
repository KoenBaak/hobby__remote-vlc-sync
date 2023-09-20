from socket import socket, AF_INET, SOCK_STREAM
import platform
import struct

from PyQt5 import QtWidgets, QtGui, QtCore
import vlc


SERVER_ADDR = ("localhost", 5000)


class MySlider(QtWidgets.QSlider):
    # custom slider class, stolen from
    # https://stackoverflow.com/questions/52689047/moving-qslider-to-mouse-click-position
    def mousePressEvent(self, event):
        if event.button() == QtCore.Qt.LeftButton:
            val = self.pixelPosToRangeValue(event.pos())
            self.setValue(val)
        super().mousePressEvent(event)

    def pixelPosToRangeValue(self, pos):
        opt = QtWidgets.QStyleOptionSlider()
        self.initStyleOption(opt)
        gr = self.style().subControlRect(
            QtWidgets.QStyle.CC_Slider, opt, QtWidgets.QStyle.SC_SliderGroove, self
        )
        sr = self.style().subControlRect(
            QtWidgets.QStyle.CC_Slider, opt, QtWidgets.QStyle.SC_SliderHandle, self
        )

        if self.orientation() == QtCore.Qt.Horizontal:
            sliderLength = sr.width()
            sliderMin = gr.x()
            sliderMax = gr.right() - sliderLength + 1
        else:
            sliderLength = sr.height()
            sliderMin = gr.y()
            sliderMax = gr.bottom() - sliderLength + 1
        pr = pos - sr.center() + sr.topLeft()
        p = pr.x() if self.orientation() == QtCore.Qt.Horizontal else pr.y()
        return QtWidgets.QStyle.sliderValueFromPosition(
            self.minimum(),
            self.maximum(),
            p - sliderMin,
            sliderMax - sliderMin,
            opt.upsideDown,
        )


# -------------------------------------------------------------------------------


class Player(QtWidgets.QMainWindow):
    def __init__(self, name, target_file, subtitle_file, master=None):
        QtWidgets.QMainWindow.__init__(self, master)
        self.setFocusPolicy(QtCore.Qt.StrongFocus)

        self.name = name
        self.target_file = target_file
        self.subtitle_file = subtitle_file

        # vlc stuff
        self.vlc_instance = vlc.Instance("--quiet")
        self.media_player = self.vlc_instance.media_player_new()
        self.media = self.vlc_instance.media_new(self.target_file)
        if self.subtitle_file is not None:
            self.media.add_options("sub-file={}".format(self.subtitle_file))
        self.media_player.set_media(self.media)
        self.playing = False
        self.is_fullscreen = False

        # internet stuff
        self.sock = None
        self.connected = False

        # ui
        self.build_ui()
        self.layout_margins = (
            self.vboxlayout.getContentsMargins()
        )  # save for restoring after fullscreen

        # update the interface every 100 ms
        self.timer = QtCore.QTimer(self)
        self.timer.setInterval(100)
        self.timer.timeout.connect(self.update_ui)

    def build_ui(self):
        # build the user interface
        self.widget = QtWidgets.QWidget(self)
        self.setCentralWidget(self.widget)

        # In this widget, the video will be drawn
        if platform.system() == "Darwin":  # for MacOS
            self.videoframe = QtWidgets.QMacCocoaViewContainer(0)
        else:
            self.videoframe = QtWidgets.QFrame()  # for Linux

        # The media player has to be 'connected' to the QFrame
        if platform.system() == "Linux":  # for Linux using the X Server
            self.media_player.set_xwindow(int(self.videoframe.winId()))
        elif platform.system() == "Darwin":  # for MacOS
            self.media_player.set_nsobject(int(self.videoframe.winId()))

        self.palette = self.videoframe.palette()
        self.palette.setColor(QtGui.QPalette.Window, QtGui.QColor(0, 0, 0))
        self.videoframe.setPalette(self.palette)
        self.videoframe.setAutoFillBackground(True)

        self.positionslider = MySlider(QtCore.Qt.Horizontal, self)
        self.positionslider.setToolTip("Position")
        self.positionslider.setMaximum(1000)
        self.positionslider.sliderMoved.connect(self.set_position)
        self.positionslider.sliderPressed.connect(self.set_position)

        self.hbuttonbox = QtWidgets.QHBoxLayout()
        self.playbutton = QtWidgets.QPushButton("Play")
        self.hbuttonbox.addWidget(self.playbutton)
        self.playbutton.clicked.connect(lambda x: self.play_pause(True))

        self.fullscreenbutton = QtWidgets.QPushButton("Fullscreen")
        self.hbuttonbox.addWidget(self.fullscreenbutton)
        self.fullscreenbutton.clicked.connect(self.fullscreen)

        self.hbuttonbox.addStretch(1)
        self.volumeslider = MySlider(QtCore.Qt.Horizontal, self)
        self.volumeslider.setMaximum(100)
        self.volumeslider.setValue(75)
        self.set_volume(75)
        self.volumeslider.setToolTip("Volume")
        self.hbuttonbox.addWidget(self.volumeslider)
        self.volumeslider.valueChanged.connect(self.set_volume)

        self.vboxlayout = QtWidgets.QVBoxLayout()
        self.vboxlayout.addWidget(self.videoframe)
        self.vboxlayout.addWidget(self.positionslider)
        self.vboxlayout.addLayout(self.hbuttonbox)

        self.widget.setLayout(self.vboxlayout)

    def connect(self, room_name, room_password, new_room=False):
        # connect to the server
        self.sock = socket(AF_INET, SOCK_STREAM)
        self.sock.connect(SERVER_ADDR)
        if new_room:
            info = "new;;{};;{};;{}".format(room_name, room_password, self.name)
        else:
            info = "join;;{};;{};;{}".format(room_name, room_password, self.name)
        self.sock.send(info.encode())  # send info to the server
        response = self.sock.recv(2048).decode()  # wait for response
        if "succes" in response:
            self.connected = True
        else:
            self.sock.close()
        return response

    def send_msg(self, msg):
        # send a message
        raw_msg = msg.encode()
        self.sock.sendall(struct.pack(">I", len(raw_msg)) + raw_msg)

    def recv_msg(self):
        # receive a message
        raw_msg_length = self.sock.recv(4)
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
            packet = self.sock.recv(n - len(data))
            if not packet:
                return None
            data.extend(packet)
        return data

    def recv_thread(self):
        while self.connected:
            msg = self.recv_msg().split(
                ";;"
            )  # self.sock.recv(2048).decode().split(";;")
            if msg[0] in ["room_enter", "room_leave"]:
                self.print_terminal(msg[1])
            elif msg[0] in ["pause", "play"]:
                self.play_pause(False)
                self.print_terminal("{} pressed {}.".format(msg[-1], msg[0]))
            elif msg[0] == "change_time":
                self.media_player.set_time(int(msg[1]))

    def start(self):
        self.media_player.play()  # start playing
        while not self.media_player.is_playing():  # wait till playing is started
            continue
        self.media_player.pause()  # pause player
        self.send_msg("state_request")
        response = self.recv_msg().split(";;")
        self.media_player.set_time(int(response[1]))
        self.positionslider.setValue(int(self.media_player.get_position() * 1000))
        if response[0] == "playing":
            self.media_player.play()
            self.playbutton.setText("Pause")
            self.playing = True
            self.timer.start()
        # print(self.media.get_duration())
        # print(self.media_player.video_get_spu_description())

    def update_ui(self):
        # update the user interface
        # Set the slider's position to its corresponding media position
        media_pos = int(self.media_player.get_position() * 1000)
        self.positionslider.setValue(media_pos)

    def play_pause(self, share):
        # toggle play/pause
        self.playing = not self.playing
        if self.media_player.is_playing():
            self.media_player.pause()
            self.playbutton.setText("Play")
            if share:
                time = self.media_player.get_time()
                self.send_msg("pause;;{};;{}".format(time, self.name))
                self.print_terminal("You pressed pause")
        else:
            self.media_player.play()
            self.playbutton.setText("Pause")
            if share:
                self.send_msg("play;;{}".format(self.name))
            self.print_terminal("You pressed play")

    def fullscreen(self):
        # the fullscreen button is pressed
        self.timer.stop()
        self.positionslider.setVisible(False)
        self.volumeslider.setVisible(False)
        self.playbutton.setVisible(False)
        self.fullscreenbutton.setVisible(False)
        self.showFullScreen()
        self.is_fullscreen = True
        self.vboxlayout.setContentsMargins(0, 0, 0, 0)
        self.fullscreenbutton.clearFocus()
        self.setCursor(QtCore.Qt.BlankCursor)

    def close_fullscreen(self):
        self.positionslider.setVisible(True)
        self.volumeslider.setVisible(True)
        self.playbutton.setVisible(True)
        self.fullscreenbutton.setVisible(True)
        self.showNormal()
        self.is_fullscreen = False
        self.vboxlayout.setContentsMargins(*self.layout_margins)
        self.timer.start()
        self.setCursor(QtCore.Qt.ArrowCursor)

    def set_volume(self, volume):
        self.media_player.audio_set_volume(volume)

    def set_position(self):
        # set media position to the position of the position slider
        self.timer.stop()
        pos = self.positionslider.value()
        self.media_player.set_position(pos / 1000.0)
        self.timer.start()
        self.send_msg("change_time;;{}".format(self.media_player.get_time()))

    def jump(self, amount):
        new_time = self.media_player.get_time() + amount * 1000
        new_time = max(0, new_time)
        self.media_player.set_time(new_time)
        self.send_msg("change_time;;{}".format(self.media_player.get_time()))

    def print_terminal(self, msg):
        print("\n\033[34m" + msg + "\033[0m")

    def closeEvent(self, event):
        self.connected = False  # needed to make the receive thread stop
        self.send_msg("bye")  # let the server know I dying
        self.media_player.stop()
        self.sock.close()

    def keyPressEvent(self, event):
        if event.key() == QtCore.Qt.Key_Escape and self.is_fullscreen:
            self.close_fullscreen()
        elif event.key() == QtCore.Qt.Key_Space:
            self.play_pause(True)
        elif event.key() == QtCore.Qt.Key_Left:
            self.jump(-10)
        elif event.key() == QtCore.Qt.Key_Right:
            self.jump(10)
