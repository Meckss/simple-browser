import base64
import os
import socket
import ssl
import sys
import urllib.parse

class browser:
    def __init__(self, url):
        self.scheme, url = url.split(":", 1)
        assert self.scheme in ["http", "https", "file", "data"]
            
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
        
        
    def request(self):
        if self.scheme == "data":
            try:
                metadata, data = self.data.split(",", 1)
            except ValueError:
                print("Invalid data URL")
                sys.exit(1)
            
            is_base64 = metadata.endswith(";base64")
            if is_base64:
                try:
                    content = base64.b64decode(data)
                except ValueError:
                    print("Invalid base64 data URL")
                    sys.exit(1)
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
            except FileNotFoundError:
                print(f"File not found: {self.path}")
                sys.exit(1)
            except PermissionError:
                print(f"Permission denied: {self.path}")
                sys.exit(1)
        s = socket.socket(
            family=socket.AF_INET,
            type=socket.SOCK_STREAM,
            proto=socket.IPPROTO_TCP
        )
        
        s.connect((self.host, self.port))
        
        if self.scheme == "https":
            ctx = ssl.create_default_context()
            s = ctx.wrap_socket(s, server_hostname=self.host)
        
        headers = {
            "Host": self.host,
            "Connection": "close",
            "User-Agent": "Mecks"
        }
        
        
        request = "GET {} HTTP/1.0\r\n".format(self.path)
        for header, value in headers.items():
            request += f"{header}: {value}\r\n"
        request += "\r\n"
        
        s.send(request.encode("utf8"))
        
        response = s.makefile("r", encoding="utf8", newline ="\r\n")
        
        statusline = response.readline()
        version, status, explanation = statusline.split(" ", 2)
                
        response_headers = {}
        while True:
            line = response.readline()
            if line == "\r\n" :
                break
            header, value = line.split(":", 1)
            response_headers[header.casefold()] = value.strip()
        
        assert "transfer-encoding" not in response_headers
        assert "content-encoding" not in response_headers 
        
        content = response.read()       
        s.close()
        
        return content
    
def show(body):
    in_tag = False
    for c in body:
        if c == "<":
            in_tag = True
        elif c == ">":
            in_tag = False
        elif not in_tag:
            print(c, end= "")
    print()
            
def load(url):
    body = url.request()
    show(body)

if __name__ == "__main__":
    if len(sys.argv) > 1:
        load(browser(sys.argv[1]))
    else:
        print("Usage: python browser.py <url>")
        print("Examples:")
        print(" python browser.py https://example.com")
        print(" python browser.py file:///path/to/file.html")
        sys.exit(1)