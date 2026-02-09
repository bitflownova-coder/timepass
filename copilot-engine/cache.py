"""
In-memory LRU cache layer for Copilot Engine.
Eliminates redundant computation for frequently accessed data.
"""
import time
import hashlib
import logging
from typing import Any, Optional, Dict, Callable
from functools import wraps
from collections import OrderedDict
from threading import Lock

logger = logging.getLogger(__name__)


class LRUCache:
    """Thread-safe LRU cache with TTL support."""

    def __init__(self, max_size: int = 256, default_ttl: int = 300):
        self.max_size = max_size
        self.default_ttl = default_ttl  # seconds
        self._cache: OrderedDict[str, Dict[str, Any]] = OrderedDict()
        self._lock = Lock()
        self._hits = 0
        self._misses = 0

    def get(self, key: str) -> Optional[Any]:
        with self._lock:
            if key in self._cache:
                entry = self._cache[key]
                if entry["expires_at"] > time.time():
                    self._cache.move_to_end(key)
                    self._hits += 1
                    return entry["value"]
                else:
                    del self._cache[key]
            self._misses += 1
            return None

    def set(self, key: str, value: Any, ttl: Optional[int] = None):
        ttl = ttl if ttl is not None else self.default_ttl
        with self._lock:
            if key in self._cache:
                self._cache.move_to_end(key)
            self._cache[key] = {
                "value": value,
                "expires_at": time.time() + ttl,
            }
            while len(self._cache) > self.max_size:
                self._cache.popitem(last=False)

    def invalidate(self, key: str):
        with self._lock:
            self._cache.pop(key, None)

    def invalidate_prefix(self, prefix: str):
        """Remove all entries whose key starts with *prefix*."""
        with self._lock:
            keys = [k for k in self._cache if k.startswith(prefix)]
            for k in keys:
                del self._cache[k]

    def clear(self):
        with self._lock:
            self._cache.clear()
            self._hits = 0
            self._misses = 0

    @property
    def stats(self) -> Dict[str, Any]:
        total = self._hits + self._misses
        return {
            "size": len(self._cache),
            "max_size": self.max_size,
            "hits": self._hits,
            "misses": self._misses,
            "hit_rate": round(self._hits / total, 3) if total else 0,
        }


def make_key(*parts: Any) -> str:
    """Create a deterministic cache key from arbitrary parts."""
    raw = "|".join(str(p) for p in parts)
    return hashlib.md5(raw.encode()).hexdigest()


# ── Global caches ─────────────────────────────────────────────

# Short-lived cache for API responses (file scans, git diffs, etc.)
response_cache = LRUCache(max_size=512, default_ttl=30)

# Longer-lived cache for project metadata (language, framework detection)
project_cache = LRUCache(max_size=64, default_ttl=600)

# Security scan results (invalidated on file change)
security_cache = LRUCache(max_size=256, default_ttl=120)


def cached(cache: LRUCache, ttl: Optional[int] = None):
    """Decorator that caches the return value of a function."""

    def decorator(fn: Callable):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            key = make_key(fn.__qualname__, args, tuple(sorted(kwargs.items())))
            result = cache.get(key)
            if result is not None:
                return result
            result = fn(*args, **kwargs)
            cache.set(key, result, ttl)
            return result

        wrapper.cache = cache  # expose for manual invalidation
        return wrapper

    return decorator
