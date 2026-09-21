"""HTTP request and response decoding."""

import gzip
import urllib.parse
import zlib

from .connection import ConnectionPool


class HTTPClient:
    REDIRECT_STATUSES = {301, 302, 303, 307, 308}

    def __init__(self, connections=None):
        self.connections = connections or ConnectionPool()

    def get(self, page):
        sock = self.connections.get(page)
        headers = {
            "Host": page.host,
            "Connection": "keep-alive",
            "User-Agent": "Mecks",
            "Accept-Encoding": "gzip, deflate",
        }
        request = "GET {} HTTP/1.0\r\n".format(page.path)
        request += "".join(f"{name}: {value}\r\n" for name, value in headers.items())
        request += "\r\n"
        try:
            sock.sendall(request.encode("utf-8"))
            raw = self.connections.receive_until(sock, b"\r\n\r\n")
            header_data, body_start = raw.split(b"\r\n\r\n", 1)
            lines = header_data.decode("iso-8859-1").split("\r\n")
            _, status, _ = lines[0].split(" ", 2)
            response_headers = {
                header.casefold(): value.strip()
                for header, value in (line.split(":", 1) for line in lines[1:])
            }
            if int(status) in self.REDIRECT_STATUSES:
                location = response_headers.get("location")
                if location is not None:
                    page.redirect_url = urllib.parse.urljoin(
                        page.original_url, location
                    )

            if "content-length" in response_headers:
                length = int(response_headers["content-length"])
                remaining = length - len(body_start)
                content = (body_start + self.connections.receive_exactly(sock, remaining)
                           if remaining > 0 else body_start[:length])
            elif response_headers.get("transfer-encoding") == "chunked":
                content = self.connections.receive_chunked(sock, body_start)
            else:
                content = body_start
                while True:
                    chunk = sock.recv(4096)
                    if not chunk:
                        break
                    content += chunk
                self.connections.discard(page, sock)
            content = self._decode_content(
                content, response_headers.get("content-encoding", "").casefold()
            )
            if response_headers.get("connection", "").casefold() == "close":
                self.connections.discard(page, sock)
            return content.decode("utf-8", errors="replace")
        except (ConnectionError, BrokenPipeError, ConnectionResetError, OSError):
            self.connections.discard(page, sock)
            raise

    def post(self, page, payload):
        """Send a form-urlencoded POST request and return its response body.

        Args:
            page: The HTTP or HTTPS resource receiving the request.
            payload: A UTF-8 string containing form-encoded request data.

        Returns:
            str: The response body decoded as UTF-8 text.
        """
        sock = self.connections.get(page)
        headers = {
            "Host": page.host,
            "Connection": "keep-alive",
            "User-Agent": "Mecks",
            "Accept-Encoding": "gzip, deflate",
            "Content-Type": "application/x-www-form-urlencoded",
            "Content-Length": str(len(payload.encode("utf-8"))),
        }
        request = "POST {} HTTP/1.0\r\n".format(page.path)
        request += "".join(f"{name}: {value}\r\n" for name, value in headers.items())
        request += "\r\n"
        try:
            sock.sendall(request.encode("utf-8") + payload.encode("utf-8"))
            raw = self.connections.receive_until(sock, b"\r\n\r\n")
            header_data, body_start = raw.split(b"\r\n\r\n", 1)
            lines = header_data.decode("iso-8859-1").split("\r\n")
            _, status, _ = lines[0].split(" ", 2)
            response_headers = {
                header.casefold(): value.strip()
                for header, value in (line.split(":", 1) for line in lines[1:])
            }
            if int(status) in self.REDIRECT_STATUSES:
                location = response_headers.get("location")
                if location is not None:
                    page.redirect_url = urllib.parse.urljoin(
                        page.original_url, location
                    )

            if "content-length" in response_headers:
                length = int(response_headers["content-length"])
                remaining = length - len(body_start)
                content = (body_start + self.connections.receive_exactly(sock, remaining)
                           if remaining > 0 else body_start[:length])
            elif response_headers.get("transfer-encoding") == "chunked":
                content = self.connections.receive_chunked(sock, body_start)
            else:
                content = body_start
                while True:
                    chunk = sock.recv(4096)
                    if not chunk:
                        break
                    content += chunk
                self.connections.discard(page, sock)
            content = self._decode_content(
                content, response_headers.get("content-encoding", "").casefold()
            )
            if response_headers.get("connection", "").casefold() == "close":
                self.connections.discard(page, sock)
            return content.decode("utf-8", errors="replace")
        except (ConnectionError, BrokenPipeError, ConnectionResetError, OSError):
            self.connections.discard(page, sock)
            raise


    @staticmethod
    def _decode_content(content, encoding):
        if encoding in ("", "identity"):
            return content
        if encoding == "gzip":
            try:
                return gzip.decompress(content)
            except OSError as error:
                raise RuntimeError("Invalid gzip response") from error
        if encoding == "deflate":
            try:
                return zlib.decompress(content)
            except zlib.error:
                try:
                    return zlib.decompress(content, -zlib.MAX_WBITS)
                except zlib.error as error:
                    raise RuntimeError("Invalid deflate response") from error
        raise RuntimeError(f"Unsupported content encoding: {encoding}")
