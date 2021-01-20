import socket
from message import Message, HostType, MessageType
import logging
from logger import prepare_logger
import key_gen
import tracker
from _thread import *
import server
import files
import utils
import os
from time import sleep

default_port = 7854

class Client:
    def __init__(self, key, trackers):
        self.s = None
        self.trackers = []
        self.key = key
        self.trackers = tracker.prepare_trackers(trackers)
        #self.open_connections = 100
        self.servers = []
        #self.clients = []
        #self.connected_clients = []
        self.backup_directory = "\\BACKUP\\" + key


    def start(self):
        self.s = socket.socket()
        #self.s.setblocking(False)
        try:
            self.run()
        except KeyboardInterrupt:
            self.shutdown()

    def shutdown(self):
        self.s.close()
        logging.info("Shut down")

    def restart_socket(self):
        self.s.close()
        self.s = socket.socket()
        #self.s.setblocking(False)

    def is_connected_to_host(self, sock, ip, port):
        try:
            return sock.getpeername() == (ip, port)
        except:
            pass
        return False

    def connect_to_host(self, sock, ip, port):
        if self.is_connected_to_host(sock, ip, port):
            return True
        try:
            sock.connect((ip, port))
            return True
        except socket.error as exc:
            logging.info("Caught exception socket.error when connecting: %s" % exc)
        return False

    def retrieve_servers_from_tracker(self, sock):
        msg = Message.encode(MessageType.Request.value, (HostType.CLIENT.value, sock.getsockname()[1], self.key))
        sock.send(msg)
        payload = sock.recv(1024);
        msg = Message.decode(payload)
        if msg:
            self.servers.extend(utils.get_complement_values_from_list(msg, self.servers))
            logging.info(f'Retrieved servers\' addresses: {msg}')
        else:
            logging.info("No servers connected to tracker on key")

    def retrieve_servers_from_trackers(self):
        while True:
            for tr in self.trackers:
                logging.info(
                    "Trying to retrieve connected server hosts from tracker %s:%s" % (
                        tr["ip"], tr["port"]))
                if self.connect_to_host(tr["socket"], tr["ip"], tr["port"]):
                    self.retrieve_servers_from_tracker(tr["socket"])
                    return

    def listen_for_incoming_files(self):
        logging.info("Started thread: listening for incoming files")
        msg = self.s.recv(files.BUFFER_SIZE)
        filename, file_size, bytesread, file_part = Message.decode(msg)
        other_filename = filename
        downloaded_bytes = 0
        while file_part:
            file_save_location = files.get_save_location(other_filename, self.backup_directory)
            files.make_dirs(file_save_location)
            file = open(file_save_location, "wb")
            while filename == other_filename:
                downloaded_bytes += bytesread
                logging.info(f"Downloading file {filename}: {downloaded_bytes} / {file_size}")
                file.write(file_part)
                #print(os.stat(filename).st_size)
                msg = self.s.recv(files.BUFFER_SIZE)
                #print(msg)
                other_filename, file_size, bytesread, file_part = Message.decode(msg)
            file.close()
            filename = other_filename
            downloaded_bytes = 0
        logging.info("All files has been received")

    def establish_connection_with_server(self):
        for serv in self.servers:
            self.restart_socket()
            self.connect_to_host(self.s, serv[0], serv[1])
            logging.info("Established connection with %s:%s" % (serv[0], serv[1]))
            self.listen_for_incoming_files()
            return

    def run(self):
        start_new_thread(self.retrieve_servers_from_trackers, ())
        while True:
            self.establish_connection_with_server()


if __name__ == '__main__':
    prepare_logger(HostType.CLIENT.name)
    trackers = [("127.0.0.1", tracker.default_tracker_port)]
    client = Client(key_gen.gen_key(), trackers)
    client.start()

