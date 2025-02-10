from typing import Any, Dict, Optional
from datetime import datetime, timedelta
import time

class CacheEntry:
    def __init__(self, value: Any, ttl: Optional[int] = None):
        self.value = value
        self.expires_at = time.time() + ttl if ttl else None

    def is_expired(self) -> bool:
        if self.expires_at is None:
            return False
        return time.time() > self.expires_at

class MemoryCache:
    def __init__(self):
        self._cache: Dict[str, CacheEntry] = {}

    def get(self, key: str) -> Optional[Any]:
        """Get a value from cache"""
        entry = self._cache.get(key)
        if entry is None:
            return None
            
        if entry.is_expired():
            del self._cache[key]
            return None
            
        return entry.value

    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        """Set a value in cache with optional TTL in seconds"""
        self._cache[key] = CacheEntry(value, ttl)

    def delete(self, key: str) -> None:
        """Delete a value from cache"""
        self._cache.pop(key, None)

    def clear(self) -> None:
        """Clear all values from cache"""
        self._cache.clear()

    def cleanup(self) -> None:
        """Remove all expired entries"""
        current_time = time.time()
        expired_keys = [
            key for key, entry in self._cache.items()
            if entry.expires_at and current_time > entry.expires_at
        ]
        for key in expired_keys:
            del self._cache[key] 