"""Reusable TCP/TLS connections and socket reading helpers."""

import socket
import ssl


class ConnectionPool:
    def __init__(self):
        self.connections = {}

    def get(self, url):
        key = url.connection_key()
        if key in self.connections:
            return self.connections[key]
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM, socket.IPPROTO_TCP)
        sock.connect((url.host, url.port))
        if url.scheme == "https":
            context = ssl.create_default_context()
            sock = context.wrap_socket(sock, server_hostname=url.host)
        self.connections[key] = sock
        return sock

    def discard(self, url, sock):
        self.connections.pop(url.connection_key(), None)
        sock.close()

    @staticmethod
    def receive_until(sock, marker):
        data = b""
        while marker not in data:
            chunk = sock.recv(4096)
            if not chunk:
                raise ConnectionError("Connection closed while reading response")
            data += chunk
        return data

    @staticmethod
    def receive_exactly(sock, amount):
        data = b""
        while len(data) < amount:
            chunk = sock.recv(amount - len(data))
            if not chunk:
                raise ConnectionError("Connection closed while reading body")
            data += chunk
        return data

    @staticmethod
    def receive_chunked(sock, data):
        content = b""
        while True:
            while b"\r\n" not in data:
                chunk = sock.recv(4096)
                if not chunk:
                    raise ConnectionError("Connection closed while reading chunk size")
                data += chunk
            size_line, data = data.split(b"\r\n", 1)
            chunk_size = int(size_line.decode("ascii"), 16)
            if chunk_size == 0:
                while len(data) < 2:
                    data += sock.recv(4096)
                return content
            while len(data) < chunk_size + 2:
                chunk = sock.recv(4096)
                if not chunk:
                    raise ConnectionError("Connection closed while reading chunk")
                data += chunk
            content += data[:chunk_size]
            data = data[chunk_size + 2:]
