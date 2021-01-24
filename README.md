# p2pbackup

P2pbackup application written entirely in python contributes to backing up ur data by using server to client connection and a tracker, which holds information about connected hosts on the specific key.

# Installation 

The only required module is tqdm.

# Run
Launch those apps on different machines:
- tracker.py
- server.py [-k key]
- client.py -k key



# TO DO
Global ip tests
Change server-trackers-clients into peers. Tracker, server and client can be all merged into equal peer. I didn't implement it because target machine usually is intended to either send backup or receive and store it.


