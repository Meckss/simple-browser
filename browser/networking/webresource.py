"""High-level page resource loading."""

from .connection import ConnectionPool
from .http import HTTPClient
from .resources import load_local
from .url import URL


class WebResource(URL):
    """Represent a URL and retrieve its text response."""

    _connection_pool = ConnectionPool()
    # Kept as a compatibility alias for code that inspects the connection pool.
    connections = _connection_pool.connections

    def request(self):
        """Fetch this page and return its response decoded as UTF-8 text."""
        if self.scheme in ("data", "file"):
            return load_local(self)
        return HTTPClient(self._connection_pool).get(self)
