import socket
import struct
from message import Message, HostType, MessageType
import logging
from logger import prepare_logger
import key_gen
import tracker
from _thread import *
import threading
import server
import enum
import files
import os

default_port = 7854

class Client:
    def __init__(self):
        self.s = None
        self.port = default_port
        self.tracker_port = tracker.default_tracker_port
        self.key = ""
        self.open_connections = 100
        self.servers = []
        self.connected_clients = []
        self.paths_of_files_to_backup = []
        self.ip = "localhost"
        self.backup_directory = "\\BACKUP"

    def start(self):
        self.s = socket.socket()
        #self.s.setblocking(False)
        self.run()

    def restart_socket(self):
        self.s.close()
        self.s = socket.socket()
        #self.s.setblocking(False)

    def retrieve_servers_from_tracker(self):
        self.s.connect((self.ip, self.tracker_port))
        msg = Message.encode(MessageType.Request.value, (HostType.CLIENT.value, key_gen.gen_key()))
        self.s.send(msg)
        payload = self.s.recv(1024);
        msg = Message.decode(payload)
        if msg:
            self.servers = payload
            logging.info(f'Retrieved servers\' addresses: {msg}')
        else:
            logging.info("No servers connected to tracker on key")
        self.s.close()

    def listen_for_incoming_files(self):
        logging.info("Started thread: listening for incoming files")
        msg = self.s.recv(files.BUFFER_SIZE)
        filename, file_size, bytesread, file_part = Message.decode(msg)
        other_filename = filename
        while file_part:
            file_save_location = files.get_save_location(other_filename, self.backup_directory)
            files.make_dirs(file_save_location)
            file = open(file_save_location, "wb")
            while filename == other_filename:
                logging.info(f"Downloading file {filename}: {file_size}")
                file.write(file_part)
                msg = self.s.recv(files.BUFFER_SIZE)
                other_filename, file_size, bytesread, file_part = Message.decode(msg)
            file.close()
            filename = other_filename
        logging.info("All files has been received")


    def establish_connection_with_server(self):
        self.restart_socket()
        self.s.connect((self.ip, server.default_port))
        logging.info("Established connection with %s:%s" % (self.ip, server.default_port))

    def run(self):
        self.retrieve_servers_from_tracker()
        self.establish_connection_with_server()
        start_new_thread(self.listen_for_incoming_files, ())
        while True:
            try:
                pass
            except KeyboardInterrupt:
                return

if __name__ == '__main__':
    prepare_logger(HostType.CLIENT.name)
    client = Client()
    client.start()

