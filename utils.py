import logging
import socket
import threading


def is_connected_to_host(sock, ip, port):
    try:
        return sock.getpeername() == (ip, port)
    except:
        pass
    return False


def connect_to_host(sock, ip, port):
    if is_connected_to_host(sock, ip, port):
        return True
    try:
        sock.connect((ip, port))
        return True
    except socket.error as exc:
        logging.info("Caught exception socket.error when connecting: %s" % exc)
    return False


def get_complement_values_from_list(list1, list2):
    return list(set(list1) - set(list2))


def start_new_thread(thread_function, args, daemon):
    x = threading.Thread(target=thread_function, args=args, daemon=daemon)
    x.start()
    return x

