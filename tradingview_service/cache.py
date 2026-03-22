import threading
import time
from typing import Any, Dict, Hashable, Optional, Tuple


class SimpleTTLCache:
    def __init__(self, ttl_seconds: int) -> None:
        self.ttl_seconds = ttl_seconds
        self._lock = threading.Lock()
        self._store: Dict[Hashable, Tuple[float, Any]] = {}

    def get(self, key: Hashable) -> Optional[Any]:
        with self._lock:
            entry = self._store.get(key)
            if entry is None:
                return None

            expires_at, value = entry
            if expires_at < time.time():
                self._store.pop(key, None)
                return None

            return value

    def set(self, key: Hashable, value: Any) -> None:
        with self._lock:
            self._store[key] = (time.time() + self.ttl_seconds, value)

