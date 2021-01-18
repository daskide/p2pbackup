import socket
import logging
from message import Message, HostType
from logger import prepare_logger

default_tracker_port = 6703

class Tracker:

    def __init__(self):
        self.connections = {}
        self.sock = None
        self.open_connections = 100
        self.tracker_port = default_tracker_port
        self.ip = "localhost"

    def handle_payload(self, address, host_type, host_key):
        if HostType(host_type) is HostType.SERVER:
            self.connections[host_key]["servers"].append(address)
            return Message.encode(2, self.connections[host_key]["clients"]) # TO CHANGE TO CLIENTS
        elif HostType(host_type) is HostType.CLIENT:
            self.connections[host_key]["clients"].append(address)
            return Message.encode(2, self.connections[host_key]["servers"])

    def send_message(self, conn, payload, address):
        host_type, host_key = Message.decode(payload)
        if host_key not in self.connections.keys():
            self.connections[host_key] = {"clients": [], "servers": []}
        logging.info(f"Sending connected peers info to {HostType(host_type).name} on key: {host_key}")
        msg = self.handle_payload(address, host_type, host_key)
        conn.send(msg)

    def listen_for_connections(self):
        (conn, address) = self.sock.accept()
        logging.info("Accepted a connection request from %s:%s" % (address[0], address[1]))
        payload = conn.recv(1024)
        self.send_message(conn, payload, address)
        conn.close()

    def run(self):
        while True:
            try:
                self.listen_for_connections()
            except KeyboardInterrupt:
                return

    def start(self):
        self.sock = socket.socket()
        self.sock.bind((self.ip, self.tracker_port))
        self.sock.listen(self.open_connections)
        self.run()
        self.sock.close()

if __name__ == '__main__':
    prepare_logger(HostType.TRACKER.name)
    tracker = Tracker()
    tracker.start()

