from struct import pack, unpack
from enum import Enum
import pickle
import ipaddress
import key_gen
from socket import inet_aton, inet_ntoa


class HostType(Enum):
    SERVER = 0
    CLIENT = 1
    TRACKER = 2


class MessageType(Enum):
    Request = 0
    File = 1
    PeersMessage = 2


class Request:
    key_length = key_gen.key_length
    host_type_length = 1

    @staticmethod
    def decode(payload_length, payload):
        (host_type, key) = unpack(">?{}s".format(Request.key_length), payload)
        return host_type, key.decode()

    @staticmethod
    def encode(msg_id, payload):
        host_type, key = payload
        key = bytes(key, 'UTF-8')
        return pack(">HH?{}s".format(Request.key_length), msg_id, Request.key_length + Request.host_type_length, host_type, key)


class FileTransfer:

    filesize_length = 4
    bytesread_length = 2

    total_metadata_length = filesize_length + bytesread_length

    @staticmethod
    def decode_additional_metadata(payload):
        (file_size,) = unpack(">I", payload[:FileTransfer.filesize_length])
        (bytesread,) = unpack(">H", payload[FileTransfer.filesize_length:FileTransfer.total_metadata_length])
        return (file_size, bytesread)

    @staticmethod
    def decode_payload(fn_length, bytesread, payload):
        (filename,) = unpack(">{}s".format(fn_length),
                             payload[:fn_length])
        (file,) = unpack(">{}s".format(bytesread), payload[fn_length:])
        return (filename, file)

    @staticmethod
    def decode(fn_length, payload):
        (file_size, bytesread) = FileTransfer.decode_additional_metadata(payload)
        (filename, file) = FileTransfer.decode_payload(fn_length, bytesread, payload[FileTransfer.total_metadata_length:])

        return filename.decode("utf-8"), file_size, bytesread, file

    @staticmethod
    def encode(msg_id, payload):
        filename, filesize, bytesread = payload
        fn_length = len(filename)
        bs_length = len(bytesread)
        return pack(">HHIH{}s{}s".format(fn_length, bs_length), msg_id, fn_length, filesize, bs_length, bytes(filename, 'UTF-8'), bytesread)

class PeersMessage:
    ip_address_length = 4
    ip_port_length = 2

    @staticmethod
    def decode(payload_length, payload):
        (ips,) = unpack(">{}s".format(payload_length), payload)
        addresses = []
        for index in range(0, len(ips), PeersMessage.ip_address_length + PeersMessage.ip_port_length):
            host = inet_ntoa(ips[index:index + PeersMessage.ip_address_length])
            port = ips[index + PeersMessage.ip_address_length:index + PeersMessage.ip_address_length + PeersMessage.ip_port_length]
            (port,) = unpack(">H", port)
            addresses.append((host, port))
        return addresses

    @staticmethod
    def encode(msg_id, payload):
        final_payload = bytearray()
        for (host, port) in payload:
            final_payload.extend(inet_aton(host))
            final_payload.extend(port.to_bytes(2, 'big'))
        final_payload = bytes(final_payload)
        return pack(">HH{}s".format(len(final_payload)), msg_id, len(final_payload), final_payload)


class MessagesMap:
    @staticmethod
    def get_messages_map():
        messages_map = {
            0: Request,
            1: FileTransfer,
            2: PeersMessage
        }
        return messages_map

    @staticmethod
    def get_message_id(cls):
        for (msg_id, msg_cls) in Message.get_messages_map().items():
            if msg_cls == cls:
                return msg_id

class Message:

    id_msg_length = 2
    payload_msg_length = 2
    metadata_length = id_msg_length + payload_msg_length
    messages_map = MessagesMap.get_messages_map()

    @staticmethod
    def decode(payload):
        (message_id, payload_length) = unpack(">HH", payload[:Message.metadata_length])
        return Message.messages_map[message_id].decode(payload_length,
                                                       payload[Message.metadata_length:])

    @staticmethod
    def encode(msg_id, payload):
        return Message.messages_map[msg_id].encode(msg_id, payload)


