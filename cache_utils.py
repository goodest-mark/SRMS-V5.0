import time
from threading import Lock


class TimeCache:
    """Simple thread‑safe cache with time‑based expiration."""

    def __init__(self, default_ttl=60):
        self._data = {}
        self._lock = Lock()
        self.default_ttl = default_ttl

    def get(self, key):
        """Return cached value if still valid, else None."""
        with self._lock:
            entry = self._data.get(key)
            if entry is None:
                return None
            value, timestamp = entry
            if time.time() - timestamp > self.default_ttl:
                # Expired
                del self._data[key]
                return None
            return value

    def set(self, key, value):
        """Store a value with the current timestamp."""
        with self._lock:
            self._data[key] = (value, time.time())

    def invalidate(self, key):
        """Remove a specific key from cache."""
        with self._lock:
            if key in self._data:
                del self._data[key]

    def clear(self):
        """Clear all cached entries."""
        with self._lock:
            self._data.clear()


# Global cache instance
ranking_cache = TimeCache(default_ttl=60)
