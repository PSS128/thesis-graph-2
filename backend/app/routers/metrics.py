# backend/app/routers/metrics.py
"""
Metrics and monitoring endpoints for LLM performance tracking and cache analysis.

Endpoints:
- GET /metrics/llm - LLM performance metrics from database
- GET /metrics/cache - Cache hit rate and performance statistics
- GET /metrics/prompts - Prompt version information
"""

from __future__ import annotations

from typing import List, Dict, Any, Optional
from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from sqlmodel import Session, select, func
from datetime import datetime, timedelta

from ..db import get_session
from ..models.store import LLMMetrics
from ..services import cache
from ..prompts.version import PromptVersions

router = APIRouter(prefix="/metrics", tags=["metrics"])


# ============================================================================
# Response Schemas
# ============================================================================

class LLMMetricsSummary(BaseModel):
    """Summary statistics for LLM API calls."""
    total_calls: int
    successful_calls: int
    failed_calls: int
    cache_hits: int
    cache_misses: int
    avg_latency_ms: float
    total_input_tokens: Optional[int] = None
    total_output_tokens: Optional[int] = None
    by_prompt_type: Dict[str, Any]
    by_version: Dict[str, Any]


class CacheStats(BaseModel):
    """Cache performance statistics."""
    total_cache_entries: int
    total_requests: int
    total_hits: int
    total_misses: int
    overall_hit_rate_percent: float
    breakdown_by_type: Dict[str, Dict[str, Any]]


class PromptVersionInfo(BaseModel):
    """Information about all prompt versions."""
    active_versions: Dict[str, str]
    changelogs: Dict[str, List[Dict[str, Any]]]


# ============================================================================
# Endpoints
# ============================================================================

@router.get("/llm", response_model=LLMMetricsSummary)
def get_llm_metrics(
    hours: int = Query(24, description="Number of hours to look back", ge=1, le=720),
    session: Session = Depends(get_session)
):
    """
    Get LLM performance metrics from the database.

    Args:
        hours: Number of hours to look back (default: 24, max: 720 = 30 days)

    Returns:
        Summary of LLM API call performance
    """
    # Calculate time threshold
    since = datetime.utcnow() - timedelta(hours=hours)

    # Query all metrics within time window
    statement = select(LLMMetrics).where(LLMMetrics.created_at >= since)
    results = session.exec(statement).all()

    if not results:
        return LLMMetricsSummary(
            total_calls=0,
            successful_calls=0,
            failed_calls=0,
            cache_hits=0,
            cache_misses=0,
            avg_latency_ms=0,
            by_prompt_type={},
            by_version={}
        )

    # Calculate aggregate stats
    total_calls = len(results)
    successful = [r for r in results if r.success]
    failed = [r for r in results if not r.success]
    cache_hits = [r for r in results if r.cache_hit]
    cache_misses = [r for r in results if not r.cache_hit]

    avg_latency = sum(r.latency_ms for r in results) / total_calls if total_calls > 0 else 0
    total_input_tokens = sum(r.input_tokens or 0 for r in results)
    total_output_tokens = sum(r.output_tokens or 0 for r in results)

    # Group by prompt type
    by_prompt_type: Dict[str, Any] = {}
    prompt_types = set(r.prompt_type for r in results)

    for pt in prompt_types:
        pt_results = [r for r in results if r.prompt_type == pt]
        pt_success = [r for r in pt_results if r.success]
        pt_cache_hits = [r for r in pt_results if r.cache_hit]

        by_prompt_type[pt] = {
            "total_calls": len(pt_results),
            "successful_calls": len(pt_success),
            "failed_calls": len(pt_results) - len(pt_success),
            "cache_hits": len(pt_cache_hits),
            "avg_latency_ms": sum(r.latency_ms for r in pt_results) / len(pt_results),
            "success_rate_percent": round(len(pt_success) / len(pt_results) * 100, 2) if pt_results else 0,
            "cache_hit_rate_percent": round(len(pt_cache_hits) / len(pt_results) * 100, 2) if pt_results else 0
        }

    # Group by version
    by_version: Dict[str, Any] = {}
    versions = set(r.prompt_version for r in results)

    for version in versions:
        v_results = [r for r in results if r.prompt_version == version]
        v_success = [r for r in v_results if r.success]

        by_version[version] = {
            "total_calls": len(v_results),
            "successful_calls": len(v_success),
            "avg_latency_ms": sum(r.latency_ms for r in v_results) / len(v_results)
        }

    return LLMMetricsSummary(
        total_calls=total_calls,
        successful_calls=len(successful),
        failed_calls=len(failed),
        cache_hits=len(cache_hits),
        cache_misses=len(cache_misses),
        avg_latency_ms=round(avg_latency, 2),
        total_input_tokens=total_input_tokens if total_input_tokens > 0 else None,
        total_output_tokens=total_output_tokens if total_output_tokens > 0 else None,
        by_prompt_type=by_prompt_type,
        by_version=by_version
    )


@router.get("/cache", response_model=CacheStats)
def get_cache_stats():
    """
    Get cache performance statistics.

    Returns:
        Cache hit rates and statistics by prompt type
    """
    stats = cache.get_stats()
    return CacheStats(**stats)


@router.get("/prompts", response_model=PromptVersionInfo)
def get_prompt_versions():
    """
    Get information about all active prompt versions and their changelogs.

    Returns:
        Prompt version info and changelogs
    """
    active_versions = PromptVersions.get_all_versions()

    # Build changelogs in serializable format
    changelogs = {}
    for prompt_type in ["node_extraction", "edge_rationale", "composition", "evidence"]:
        changelog = PromptVersions.get_changelog(prompt_type)
        changelogs[prompt_type] = [
            {
                "version": v.version,
                "date_introduced": v.date_introduced,
                "changes": v.changes,
                "is_active": v.is_active
            }
            for v in changelog.values()
        ]

    return PromptVersionInfo(
        active_versions=active_versions,
        changelogs=changelogs
    )


@router.post("/cache/clear")
def clear_cache(prefix: Optional[str] = None):
    """
    Clear the cache (admin endpoint).

    Args:
        prefix: Optional prefix to clear specific cache entries (e.g., "composition")

    Returns:
        Success message
    """
    cache.clear(prefix=prefix)
    return {
        "success": True,
        "message": f"Cache cleared{' for prefix: ' + prefix if prefix else ' (all entries)'}"
    }
