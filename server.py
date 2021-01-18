import errno
import socket
import message
from message import Message, HostType, MessageType
import logging
from logger import prepare_logger
import files
import key_gen
import tracker
from _thread import *
import tqdm
import os

default_port = 31234

class Server:
    def __init__(self):
        self.s = None
        self.ip = "localhost"
        self.port = default_port
        self.tracker_port = tracker.default_tracker_port
        self.key = ""
        self.open_connections = 100
        self.clients = []
        self.connected_clients = []
        self.directories = []

    def start(self):
        self.directories.append("C:\Temp")
        self.s = socket.socket()
        self.allocate_port()
        self.s.listen(self.open_connections)
        self.run()
        self.s.close()

    def allocate_port(self):
        while not self.try_to_allocate_port():
            self.port += 1
            self.try_to_allocate_port()

    def try_to_allocate_port(self):
        try:
            self.s.bind((self.ip, self.port))
            logging.info(f"Opened socket on address: {self.s.getsockname()}")
        except socket.error as e:
            if e.errno == errno.EADDRINUSE:
                logging.info(f"Port {self.port} is already in use. Trying to find empty one")
                return False
        return True

    def retrieve_clients_from_tracker(self):
        sock = socket.socket()
        sock.connect((self.ip, self.tracker_port))
        msg = Message.encode(MessageType.Request.value, (HostType.SERVER.value, key_gen.gen_key()))
        sock.send(msg)
        payload = sock.recv(1024);
        msg = Message.decode(payload)
        if msg:
            self.clients = msg
            logging.info(f"Clients retrieved from tracker: {msg}")
        else:
            logging.info("No clients connected to tracker on key")
        sock.close()

    def send_file(self, conn, file):
        filename = file
        filesize = os.stat(file).st_size
        progress = tqdm.tqdm(range(filesize), f"Sending {filename}", unit="B", unit_scale=True,
                             unit_divisor=1024)
        with open(file, "rb") as f:
            for _ in progress:
                bytes_read = f.read(
                    files.BUFFER_SIZE - Message.metadata_length - message.FileTransfer.total_metadata_length - len(filename))
                if not bytes_read:
                    break
                msg = Message.encode(MessageType.File.value, (filename, filesize, bytes_read))
                conn.send(msg)
                progress.update(len(bytes_read))

    def send_all_files_to_client(self, conn):
        for dir in self.directories:
            for file in files.get_absolute_file_paths(dir):
                self.send_file(conn, file)
        logging.info("Sent all files")
        msg = Message.encode(MessageType.File.value, ("", 0, bytes()))
        conn.send(msg)

    def listen_for_connections(self):
        logging.info("Started thread: listening for connections")
        while True:
            (conn, address) = self.s.accept()
            logging.info("Accepted a connection request from %s:%s" % (address[0], address[1]))
            self.connected_clients.append({conn: address})
            start_new_thread(self.send_all_files_to_client, (conn,))
            # send_message(conn, payload, address)

    def run(self):
        start_new_thread(self.retrieve_clients_from_tracker, ())
        start_new_thread(self.listen_for_connections, ())
        while True:
            try:
                pass
            except KeyboardInterrupt:
                return


if __name__ == '__main__':
    prepare_logger(HostType.SERVER.name)
    server = Server()
    server.start()

