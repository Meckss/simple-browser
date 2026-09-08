import base64
import binascii
import gzip
import os
import socket
import ssl
import urllib.parse
import zlib

class Page:
    connections = {}
    
    def __init__(self, url):
        self.original_url = url
        self.redirect_url = None
        self.view_source = False
        try:
            self.scheme, url = url.split(":", 1)
        except ValueError:
            raise ValueError(
                f"Invalid URL: {url!r}. Expected a URL such as https://example.com"
            )
        
        if self.scheme == ("view-source"):
            self.view_source = True
            self.scheme, url = url.split(":", 1)
        
        if self.scheme not in ["http", "https", "file", "data"]:
            raise ValueError(f"Unsupported URL scheme: {self.scheme!r}")
            
        if self.scheme == "file":
            self.path = os.path.abspath(url)
            return
        
        if self.scheme == "data":
            self.data = url
            return
        
        url = url.lstrip("/")
        if self.scheme == "http":
            self.port = 80
        elif self.scheme == "https":
            self.port = 443
            
        if "/" not in url:
            url = url + "/"
        self.host, url = url.split("/", 1)
        if ":" in self.host:
            self.host, port = self.host.split(":", 1)
            self.port = int(port)
        self.path = "/" + url
        
    def connection_key(self):
        return self.scheme, self.host, self.port
    
    def connect(self):
        key = self.connection_key()
        
        if key in Page.connections:
            return Page.connections[key]
        
        s = socket.socket(
            family = socket.AF_INET,
            type = socket.SOCK_STREAM,
            proto = socket.IPPROTO_TCP
        )
        
        s.connect((self.host, self.port))
        
        if self.scheme == "https":
            ctx = ssl.create_default_context()
            s = ctx.wrap_socket(s, server_hostname=self.host)
        
        Page.connections[key] = s
        return s
    
    def receive_until(self, s, marker):
        data = b""
        
        while marker not in data:
            chunk = s.recv(4096)
            
            if not chunk:
                raise ConnectionError("Connection closed while reading response")
            
            data += chunk
            
        return data
    
    def receive_exactly(self, s, amount):
        data = b""
        
        while len(data) < amount:
            chunk = s.recv(amount - len(data))
        
            if not chunk:
                raise ConnectionError("Connection closed while reading body")
            
            data += chunk
        return data
        
    def read_chunked_body(self, s, data):
        content = b""

        while True:
            while b"\r\n" not in data:
                chunk = s.recv(4096)

                if not chunk:
                    raise ConnectionError("Connection closed while reading chunk size")

                data += chunk

            size_line, data = data.split(b"\r\n", 1)
            chunk_size = int(size_line.decode("ascii"), 16)

            if chunk_size == 0:
                while len(data) < 2:
                    data += s.recv(4096)

                return content

            while len(data) < chunk_size + 2:
                chunk = s.recv(4096)

                if not chunk:
                    raise ConnectionError("Connection closed while reading chunk")

                data += chunk

            content += data[:chunk_size]

            data = data[chunk_size + 2:]
        
    def resolve(self, url):
        if "://" in url: 
            return Page(url)
        if not url.startswith("/"):
            directory, _ = self.path.rsplit("/", 1)
            while url.startswith("../"):
                _, url = url.split("/", 1)
                if "/" in directory:
                    directory, _ = directory.rsplit("/", 1)
            url = directory + "/" + url
        if url.startswith("//"):
            return Page(self.scheme+ ":" + url)
        return Page(self.scheme + "://" + self.host + \
            ":" + str(self.port) + url)
        
    def request(self):
        if self.scheme == "data":
            try:
                metadata, data = self.data.split(",", 1)
            except ValueError as error:
                raise ValueError("Invalid data URL: missing comma") from error
            
            is_base64 = metadata.endswith(";base64")
            if is_base64:
                try:
                    content = base64.b64decode(data)
                except (ValueError, binascii.Error) as error:
                    raise ValueError("Invalid base64 data URL") from error
            else:
                content = urllib.parse.unquote_to_bytes(data)
            try:
                return content.decode("utf-8")
            except UnicodeDecodeError:
                return content.decode("utf-8", errors="replace")
        
        
        if self.scheme == "file":
            try:
                with open(self.path, "r", encoding="utf8") as f:
                    return f.read()
            except FileNotFoundError as error:
                raise FileNotFoundError(
                    f"File not found: {self.path}"
                ) from error
            except PermissionError as error:
                raise PermissionError(
                    f"Permission denied: {self.path}"
                ) from error
                
        s = self.connect()
                
        headers = {
            "Host": self.host,
            "Connection": "keep-alive",
            "User-Agent": "Mecks",
            "Accept-Encoding": "gzip, deflate"
        }
        
        
        request = "GET {} HTTP/1.0\r\n".format(self.path)
        for header, value in headers.items():
            request += f"{header}: {value}\r\n"
        request += "\r\n"
        
        try:
            s.sendall(request.encode("utf-8"))
            
            raw_response = self.receive_until(s, b"\r\n\r\n")
            
            header_data, body_start = raw_response.split(b"\r\n\r\n", 1)
            header_lines = header_data.decode("iso-8859-1").split("\r\n")
            
            status_line = header_lines[0]
            version, status, explanation = status_line.split(" ", 2)
            
            status_code = int(status)
            
            response_headers = {}
            
            for line in header_lines[1:]:
                header, value = line.split(":", 1)
                response_headers[header.casefold()] = value.strip()
                            
            redirect_statuses = {301, 302, 303, 307, 308}
            
            if status_code in redirect_statuses:
                location = response_headers.get("location")
                if location is not None:
                    self.redirect_url = urllib.parse.urljoin(
                        self.original_url,
                        location
                    )

            content_encoding = response_headers.get("content-encoding", "").casefold()
            if "content-length" in response_headers:
                content_length = int(response_headers["content-length"])
                remaining = content_length - len(body_start)

                if remaining > 0:
                    content = body_start + self.receive_exactly(s, remaining)
                else:
                    content = body_start[:content_length]

            elif response_headers.get("transfer-encoding") == "chunked":
                content = self.read_chunked_body(s, body_start)

            else:
                content = body_start

                while True:
                    chunk = s.recv(4096)

                    if not chunk:
                        break

                    content += chunk

                Page.connections.pop(self.connection_key(), None)
                s.close()
                
                
            if content_encoding in ("", "identity"):
                pass
            elif content_encoding == "gzip":
                try: 
                    content = gzip.decompress(content)
                except OSError as e:
                    raise RuntimeError("Invalid gzip response") from e
            elif content_encoding == "deflate":
                try:
                    content = zlib.decompress(content)
                except zlib.error:
                    try:
                        content = zlib.decompress(content, -zlib.MAX_WBITS)
                    except zlib.error as e:
                        raise RuntimeError("Invalid deflate response") from e
            else:
                raise RuntimeError(f"Unsupported content encoding: {content_encoding}")
            
            return content.decode("utf-8", errors = "replace")
            
        except (ConnectionError, BrokenPipeError, ConnectionResetError, OSError):
            Page.connections.pop(self.connection_key(), None)
            s.close()
            raise