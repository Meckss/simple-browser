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

    def request(self, payload=None):
        """Fetch this resource, optionally sending a POST payload.

        Args:
            payload: Optional UTF-8 form-encoded request body. When omitted,
                the resource is fetched with GET.

        Returns:
            str: The response body decoded as UTF-8 text.
        """
        if self.scheme in ("data", "file"):
            return load_local(self)
        client = HTTPClient(self._connection_pool)
        if payload is None:
            return client.get(self)
        return client.post(self, payload)
