"""Simple in-memory cache for LLM responses and embeddings."""
from __future__ import annotations
import hashlib
import time
from typing import Dict, Any, Optional, Tuple

# In-memory cache: {cache_key: (timestamp, value)}
_cache: Dict[str, Tuple[float, Any]] = {}

# Cache TTL in seconds
LLM_CACHE_TTL = 3600  # 1 hour for LLM responses
EMBEDDING_CACHE_TTL = 7200  # 2 hours for embedding retrievals

def _make_key(prefix: str, *args) -> str:
    """Create cache key from prefix and arguments."""
    combined = f"{prefix}::{str(args)}"
    return hashlib.md5(combined.encode("utf-8")).hexdigest()

def get(prefix: str, *args, ttl: int = LLM_CACHE_TTL) -> Optional[Any]:
    """Get cached value if exists and not expired."""
    key = _make_key(prefix, *args)
    if key not in _cache:
        return None

    timestamp, value = _cache[key]
    if time.time() - timestamp > ttl:
        # Expired, remove from cache
        del _cache[key]
        return None

    return value

def set(prefix: str, value: Any, *args) -> None:
    """Set cache value with current timestamp."""
    key = _make_key(prefix, *args)
    _cache[key] = (time.time(), value)

def clear(prefix: Optional[str] = None) -> None:
    """Clear cache. If prefix provided, only clear matching keys."""
    global _cache
    if prefix is None:
        _cache = {}
    else:
        keys_to_delete = [k for k in _cache.keys() if k.startswith(prefix)]
        for k in keys_to_delete:
            del _cache[k]

def get_stats() -> Dict[str, Any]:
    """Get cache statistics."""
    return {
        "total_entries": len(_cache),
        "cache_keys": list(_cache.keys())
    }
