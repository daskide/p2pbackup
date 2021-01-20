# p2pbackup

P2pbackup application written entirely in python contributes to backing up ur data by using peer to peer connection and a tracker, which holds information about connected peers on the specific key.

To make it work, you have to lunch
- tracker.py on dedicated server, so it can redistribute connections among peers,
- server.py which is responsible for sending ur local files to the other peers
- client.py which stores backup

Required python modules: tqdm

TO DO:
- make it work globally instead of localhost
- handle console input


