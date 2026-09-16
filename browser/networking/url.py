"""URL parsing, formatting, and relative URL resolution."""

import os


class URL:
    """Represent a supported browser URL."""

    @staticmethod
    def _normalize_url(url):
        url = url.strip()
        if len(url) >= 2 and url[-1] == "/" and url[-2] in "'\"":
            url = url[:-2]
        while url and url[0] in "'\"":
            url = url[1:].lstrip()
        while url and url[-1] in "'\"":
            url = url[:-1].rstrip()
        return url

    def __init__(self, url):
        url = self._normalize_url(url)
        self.original_url = url
        self.redirect_url = None
        self.view_source = False
        url, separator, fragment = url.partition("#")
        self.fragment = fragment if separator else None
        try:
            self.scheme, url = url.split(":", 1)
        except ValueError as error:
            raise ValueError(
                f"Invalid URL: {url!r}. Expected a URL such as https://example.com"
            ) from error
        if self.scheme == "view-source":
            self.view_source = True
            self.scheme, url = url.split(":", 1)
        if self.scheme not in ["http", "https", "file", "data"]:
            raise ValueError(
                f"Unsupported URL scheme: {self.scheme!r} in URL "
                f"{self.original_url!r}"
            )
        if self.scheme == "file":
            self.path = os.path.abspath(url)
            return
        if self.scheme == "data":
            self.data = url
            return
        url = url.lstrip("/")
        self.port = 80 if self.scheme == "http" else 443
        if "/" not in url:
            url += "/"
        self.host, url = url.split("/", 1)
        if ":" in self.host:
            self.host, port = self.host.split(":", 1)
            self.port = int(port)
        self.path = "/" + url

    def connection_key(self):
        return self.scheme, self.host, self.port

    def resolve(self, url):
        url = self._normalize_url(url)
        if url.startswith("#"):
            return self.__class__(self.original_url.split("#", 1)[0] + url)
        if "://" in url:
            return self.__class__(url)
        if url.startswith("//"):
            return self.__class__(self.scheme + ":" + url)
        if not url.startswith("/"):
            directory, _ = self.path.rsplit("/", 1)
            while url.startswith("../"):
                _, url = url.split("/", 1)
                if "/" in directory:
                    directory, _ = directory.rsplit("/", 1)
            url = directory + "/" + url
        return self.__class__(
            self.scheme + "://" + self.host + ":" + str(self.port) + url
        )

    def __str__(self):
        if self.scheme == "data":
            value = self.scheme + ":" + self.data
        elif self.scheme == "file":
            value = self.scheme + "://" + self.path
        else:
            port = ":" + str(self.port)
            if (self.scheme == "https" and self.port == 443 or
                    self.scheme == "http" and self.port == 80):
                port = ""
            value = self.scheme + "://" + self.host + port + self.path
        return value + ("#" + self.fragment if self.fragment is not None else "")
