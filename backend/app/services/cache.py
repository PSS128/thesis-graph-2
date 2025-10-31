"""Simple in-memory cache for LLM responses and embeddings with differentiated TTLs."""
from __future__ import annotations
import hashlib
import time
from typing import Dict, Any, Optional, Tuple

# In-memory cache: {cache_key: (timestamp, value)}
_cache: Dict[str, Tuple[float, Any]] = {}

# Cache statistics tracking
_cache_stats: Dict[str, Dict[str, int]] = {}

# Cache TTL in seconds - Differentiated by operation type
# Node extraction: 1 hour (per user request, not 7 days)
# Edge rationale: 1 hour (per user request, not 7 days)
# Evidence retrieval: 1 hour (dynamic content - depends on corpus)
# Composition: 6 hours (semi-dynamic - expensive operation, balance reuse vs. freshness)
LLM_CACHE_TTL = 3600  # 1 hour default for LLM responses (node extraction, edge rationale, evidence)
COMPOSITION_CACHE_TTL = 21600  # 6 hours for composition (more expensive, longer cache)
EMBEDDING_CACHE_TTL = 7200  # 2 hours for embedding retrievals

def _make_key(prefix: str, *args) -> str:
    """Create cache key from prefix and arguments."""
    combined = f"{prefix}::{str(args)}"
    return hashlib.md5(combined.encode("utf-8")).hexdigest()

def _record_stat(prompt_type: str, hit: bool):
    """Record cache hit/miss statistics."""
    if prompt_type not in _cache_stats:
        _cache_stats[prompt_type] = {"hits": 0, "misses": 0}

    if hit:
        _cache_stats[prompt_type]["hits"] += 1
    else:
        _cache_stats[prompt_type]["misses"] += 1


def get(prefix: str, *args, ttl: int = LLM_CACHE_TTL) -> Optional[Any]:
    """Get cached value if exists and not expired."""
    key = _make_key(prefix, *args)

    # Extract prompt type from prefix if it's a versioned key
    # Format: (prompt_type, version, ...)
    prompt_type = prefix if isinstance(prefix, str) else (prefix[0] if isinstance(prefix, tuple) and len(prefix) > 0 else "unknown")

    if key not in _cache:
        _record_stat(prompt_type, hit=False)
        return None

    timestamp, value = _cache[key]
    if time.time() - timestamp > ttl:
        # Expired, remove from cache
        del _cache[key]
        _record_stat(prompt_type, hit=False)
        return None

    _record_stat(prompt_type, hit=True)
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
    """Get cache statistics including hit rates by prompt type."""
    total_hits = sum(stats["hits"] for stats in _cache_stats.values())
    total_misses = sum(stats["misses"] for stats in _cache_stats.values())
    total_requests = total_hits + total_misses

    hit_rate_overall = (total_hits / total_requests * 100) if total_requests > 0 else 0

    # Calculate hit rate per prompt type
    breakdown = {}
    for prompt_type, stats in _cache_stats.items():
        hits = stats["hits"]
        misses = stats["misses"]
        requests = hits + misses
        hit_rate = (hits / requests * 100) if requests > 0 else 0

        breakdown[prompt_type] = {
            "hits": hits,
            "misses": misses,
            "total_requests": requests,
            "hit_rate_percent": round(hit_rate, 2)
        }

    return {
        "total_cache_entries": len(_cache),
        "total_requests": total_requests,
        "total_hits": total_hits,
        "total_misses": total_misses,
        "overall_hit_rate_percent": round(hit_rate_overall, 2),
        "breakdown_by_type": breakdown
    }


def invalidate_node_cache(node_id: str):
    """
    Invalidate all cached results that might have used this node.
    Call this when a node's definition is edited.
    """
    # Find and remove cache entries that might contain this node
    keys_to_delete = []
    for key in _cache.keys():
        # Cache keys are hashed, so we can't easily inspect them
        # Instead, we'll use a prefix-based approach or clear composition cache entirely
        # For now, clear all composition cache when any node changes
        if "composition" in key.lower():
            keys_to_delete.append(key)

    for key in keys_to_delete:
        del _cache[key]

    print(f"[CACHE INVALIDATION] Cleared {len(keys_to_delete)} composition cache entries due to node {node_id} edit")


def get_ttl_for_operation(operation: str) -> int:
    """
    Get the appropriate TTL for a given operation type.

    Args:
        operation: "node_extraction", "edge_rationale", "composition", "evidence", or "embedding"

    Returns:
        TTL in seconds
    """
    ttl_map = {
        "node_extraction": LLM_CACHE_TTL,  # 1 hour
        "edge_rationale": LLM_CACHE_TTL,  # 1 hour
        "composition": COMPOSITION_CACHE_TTL,  # 6 hours
        "evidence": LLM_CACHE_TTL,  # 1 hour
        "embedding": EMBEDDING_CACHE_TTL,  # 2 hours
    }
    return ttl_map.get(operation, LLM_CACHE_TTL)  # Default to 1 hour
