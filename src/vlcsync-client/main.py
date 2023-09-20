import os
import threading
import sys


from PyQt5 import QtWidgets


from player import Player


INDENT = "    "  # indentation for menu items

# define some global lambda functions,
# that can be used to format terminal output
RED = lambda x: "\033[31m" + x + "\033[0m"
GREEN = lambda x: "\033[32m" + x + "\033[0m"
YELLOW = lambda x: "\033[93m" + x + "\033[0m"
DARK_YELLOW = lambda x: "\033[33m" + x + "\033[0m"
BLUE = lambda x: "\033[34m" + x + "\033[0m"
MAGENTA = lambda x: "\033[35m" + x + "\033[0m"
CYAN = lambda x: "\033[36m" + x + "\033[0m"
UNDERLINE = lambda x: "\033[4m" + x + "\033[0m"


def subtitle_menu(filename):
    print(YELLOW("\nChoose your subtitles"))
    subs = []
    directory = os.path.dirname(filename) or "."
    for f in os.listdir(directory):
        if f.split(".")[-1] == "srt":
            subs.append(f)
    choice = -1
    while choice not in range(1, len(subs) + 2):
        print()
        print(INDENT, "1. I don't want subtitles")
        print(INDENT, "2. I will type the path to the subs")
        for c, s in enumerate(subs):
            print(INDENT, "{}. {}".format(c + 3, s))

        choice = int(input(YELLOW("choice: ")))

        if choice == 1:
            return None
        if choice == 2:
            valid_sub = False
            while not valid_sub:
                f = input(YELLOW("subtitles of the video (incl path)    : "))
                valid_sub = os.path.isfile(f)
                if not valid_sub:
                    print(RED("Invalid path, try again!"))
            return f
        if choice in range(3, len(subs) + 3):
            return directory + "/" + subs[choice - 3]
        else:
            print(RED("Invalid choice"))


def main_menu():
    name = input(YELLOW("Enter your name: "))
    print(DARK_YELLOW("NOTE: everbody should have exactly the same file"))
    valid_file = False
    while not valid_file:
        filename = input(YELLOW("filename of the video (incl path)    : "))
        valid_file = os.path.isfile(filename)
        if not valid_file:
            print(RED("Invalid path, try again!"))

    subtitle_file = subtitle_menu(filename)

    app = QtWidgets.QApplication([])
    player = Player(name, filename, subtitle_file)

    choice = -1
    while choice != 3:
        print()
        print(INDENT, "1. New room")
        print(INDENT, "2. Join room")
        print(INDENT, "3. Exit")
        choice = int(input(YELLOW("choice: ")))

        if choice == 1:
            new_or_join = "new"
        elif choice == 2:
            new_or_join = "join"
        if choice in [1, 2]:
            print()
            room_name = input(YELLOW("Room name     : "))
            room_password = input(YELLOW("Room password : "))
            print("\n" + BLUE("Connecting..."))
            connect_try = player.connect(room_name, room_password, choice == 1).split(
                ";;"
            )
            if connect_try[0] == "succes":
                print(GREEN("Connected!\n"))
                print(
                    CYAN("Currently in this room:\n")
                    + "\n".join(n for n in connect_try[1:])
                    + "\n"
                )
                print(
                    DARK_YELLOW(
                        "Starting player, please ignore potential libva log output"
                    )
                )
                player.show()  # show the player
                player.resize(640, 480)
                player.start()  # start the player in sync
                threading.Thread(
                    target=player.recv_thread
                ).start()  # start listening to the server
                app.exec_()  # wait till the player app is dead
                print("\n" + DARK_YELLOW("You left the room ") + BLUE(room_name))
                choice = 3
            else:
                print(RED(connect_try[0]))

    print(RED("bye :)"))


# -------------------------------------------------------------------------------
if __name__ == "__main__":
    if "darwin" in sys.platform:
        import subprocess

        subprocess.Popen("caffeinate")

    main_menu()
