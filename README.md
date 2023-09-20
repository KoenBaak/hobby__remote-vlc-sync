# hobby__remote-vlc-sync
Watch Movies/Shows with your friends remotely by syncing VLC players

This is an old hobby project. It was created to be able to watch TV shows together with 
friends remotely during the first COVID lockdown in April 2020. 
Uploaded to GitHub in 2023 without code changes. 

This project just syncs video players, it does not handle any actual streaming of video. So everyone needs
to have the same video file.

The player features
- synced play/pause button (also on space)
- synced moving to any point in the video
- synced forward/backward few seconds with left and right arrow
- fullscreen mode (not synced)
- audio volume (not synced)

## Running

_server_

- Make sure you set the IP and PORT variable in ``main.py``
- Make sure your (host, port) combination is available for outsiders. If 
you are hosting yourself in a local network, you will need to configure port 
forwarding on your router.
- No requirements needed, just run `main.py`

_clients_

The client is tested to work on Linux in 2023 with python 3.10. 
Back in 2020 it also worked on macOS, but not tested since. Not tested on Windows. 

- Make sure you have VLC installed correctly. Correctly means that the Python 
bindings for vlclib work. For example, on Ubuntu, installing with `snap` will not 
result in success, but installation with `apt-get` will. 
- Install the requirements
- Make sure to set the SERVER_ADDR variable in ``player.py`` to the address of the server
- Run ``main.py``