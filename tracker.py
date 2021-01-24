import socket
import logging

import utils
from message import Message, HostType, MessageType
from logger import prepare_logger
from _thread import start_new_thread
default_tracker_port = 6704


def prepare_trackers(trackers):
    tracker_list = []
    for tr in trackers:
        s = socket.socket()
        dic = tracker_to_dict(s, tr[0], tr[1])
        tracker_list.append(dic)
    return tracker_list


def tracker_to_dict(socket, ip, port):
    return {"socket": socket, "ip": ip, "port": port}


class Tracker:

    def __init__(self):
        self.connections = {}
        self.sock = None
        self.open_connections = 100
        self.tracker_port = default_tracker_port
        self.ip = "localhost"

    def handle_payload(self, host_ip, host_port, host_type, host_key):
        if HostType(host_type) is HostType.SERVER:
            self.connections[host_key]["servers"].append((host_ip, host_port))
            #self.connections[host_key]["servers"].extend(utils.get_complement_values_from_list([(host_ip, host_port)], self.connections[host_key]["servers"]))
            return Message.encode(MessageType.PeersMessage.value, self.connections[host_key]["clients"])
        elif HostType(host_type) is HostType.CLIENT:
            self.connections[host_key]["clients"].append((host_ip, host_port))
            #self.connections[host_key]["clients"].extend(
            #    utils.get_complement_values_from_list([(host_ip, host_port)], self.connections[host_key]["clients"]))
            return Message.encode(MessageType.PeersMessage.value, self.connections[host_key]["servers"])

    def send_message_about_connected_hosts(self, conn, payload, host_ip):
        host_type, host_port, host_key = Message.decode(payload)
        if host_key not in self.connections.keys():
            self.connections[host_key] = {"clients": [], "servers": []}
        logging.info(f"Sending connected peers info to {HostType(host_type).name} on key: {host_key}")
        msg = self.handle_payload(host_ip, host_port, host_type, host_key)
        conn.send(msg)

    def listen_for_message(self, conn, address):
        while True:
            payload = conn.recv(1024)
            if len(payload) > Message.id_msg_length + Message.metadata_length + Message.payload_msg_length:
                self.send_message_about_connected_hosts(conn, payload, address[0])
        conn.close()

    def listen_for_connections(self):
        (conn, address) = self.sock.accept()
        logging.info("Accepted a connection request from %s:%s" % (address[0], address[1]))
        start_new_thread(self.listen_for_message, (conn, address))

    def run(self):
        while True:
            try:
                self.listen_for_connections()
            except KeyboardInterrupt:
                return

    def start(self):
        self.sock = socket.socket()
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.sock.bind((self.ip, self.tracker_port))
        self.sock.listen(self.open_connections)
        self.run()
        self.sock.close()

if __name__ == '__main__':
    prepare_logger(HostType.TRACKER.name)
    tracker = Tracker()
    tracker.start()

