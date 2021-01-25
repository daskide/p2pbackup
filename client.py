import socket
import tqdm
from time import sleep
import sys
import getopt

from message import Message, HostType, MessageType
from logger import prepare_logger
import tracker
import logging
import files
import utils
import threading


default_port = 7854


class Client:
    def __init__(self, key, backup_dir, trackers):
        self.s = None
        self.trackers = []
        self.key = key
        self.trackers = tracker.prepare_trackers(trackers)
        #self.open_connections = 100
        self.servers = []
        #self.clients = []
        self.backup_directory = backup_dir


    def start(self):
        self.s = socket.socket()
        logging.info("Host's key: " + self.key)
        logging.info("Backup directory: " + self.backup_directory)
        try:
            self.run()
        except KeyboardInterrupt:
            pass
        self.shutdown()

    def shutdown(self):
        self.close_all_sockets()
        logging.info("Shut down")

    def close_all_sockets(self):
        self.s.close()
        for tr in self.trackers:
            tr["socket"].close()

    def restart_socket(self):
        self.s.close()
        self.s = socket.socket()

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
                if utils.connect_to_host(tr["socket"], tr["ip"], tr["port"]):
                    self.retrieve_servers_from_tracker(tr["socket"])
            sleep(20)

    def download_incoming_files(self):
        logging.info("Started thread: listening for incoming files")
        msg = self.s.recv(files.BUFFER_SIZE)
        filename, file_size, bytesread, file_part = Message.decode(msg)
        other_filename = filename
        downloaded_bytes = 0

        while file_part:
            file_save_location = files.get_save_location(other_filename, self.backup_directory)
            files.make_dirs(file_save_location)
            file = open(file_save_location, "wb")
            progress = tqdm.tqdm(range(file_size), f"Receiving {filename}", unit="B", unit_scale=True,
                                 unit_divisor=1024)
            while filename == other_filename:
                downloaded_bytes += bytesread
                file.write(file_part)
                msg = self.s.recv(files.BUFFER_SIZE)
                if len(msg) > Message.id_msg_length:
                    other_filename, file_size, bytesread, file_part = Message.decode(msg)
                    progress.update(len(file_part))
                else:
                    file_part = 0
                    break
            progress.close()
            file.close()
            filename = other_filename
            downloaded_bytes = 0
        logging.info("All files have been received")

    def establish_connection_with_server(self):
        while True:
            for serv in self.servers:
                self.restart_socket()
                utils.connect_to_host(self.s, serv[0], serv[1])
                logging.info("Established connection with %s:%s" % (serv[0], serv[1]))
                self.download_incoming_files()
                return
            sleep(10)

    def handle_input(self):
        while True:
            inp = input("Enter \"quit\": to quit\n")
            if inp == "quit":
                return False
            return True

    def run(self):
        utils.start_new_thread(self.retrieve_servers_from_trackers, (), True)
        utils.start_new_thread(self.establish_connection_with_server, (), True)
        self.handle_input()


def print_help():
    print('client.py -k key [-b backup_dir] [-d]:\n'
          'key - same key as the server which is used to get server\'s ip from a tracker\n'
          'backup_dir - dir to backup data\n'
          'd - flag to add key to directory path')


def parse_arguments(argv):
    key = ''
    backup_dir = "C:\\BACKUP\\"
    key_to_dir = False

    try:
        opts, args = getopt.getopt(argv, "hk:b:d", ["key=", "backup_dir="])
    except getopt.GetoptError:
        print_help()
        sys.exit(2)
    for opt, arg in opts:
        if opt == '-h':
            print_help()
            sys.exit()
        elif opt in ("-k", "--key"):
            key = arg
        elif opt in ("-b", "--backup_dir"):
            backup_dir = arg
        elif opt in ("-d", "--key_to_dir"):
            key_to_dir = True
    if key == '':
        print_help()
        sys.exit()
    if key_to_dir is True:
        backup_dir += key
    return key, backup_dir


if __name__ == '__main__':
    key, backup_dir = parse_arguments(sys.argv[1:])
    prepare_logger(HostType.CLIENT.name)
    trackers = [("127.0.0.1", tracker.default_tracker_port)]
    client = Client(key, backup_dir, trackers)
    client.start()

