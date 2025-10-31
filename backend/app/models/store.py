# backend/app/models/store.py
from __future__ import annotations

from datetime import datetime
from typing import Optional
from sqlmodel import SQLModel, Field


class User(SQLModel, table=True):
    """User account for authentication"""
    id: Optional[int] = Field(default=None, primary_key=True)
    email: str = Field(unique=True, index=True)
    hashed_password: str
    created_at: datetime = Field(default_factory=datetime.utcnow)
    is_active: bool = True


class Project(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="user.id", index=True)
    title: str
    created_at: datetime = Field(default_factory=datetime.utcnow)


class GraphNode(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    project_id: int = Field(index=True)
    node_id: str = Field(index=True, unique=True)

    # Core fields
    name: str  # Canonical variable name
    kind: str = Field(default="VARIABLE")  # "THESIS" | "VARIABLE" | "ASSUMPTION"
    definition: Optional[str] = None  # Short definition

    # Legacy field (kept for backward compatibility)
    text: Optional[str] = None
    type: Optional[str] = None  # Deprecated: use 'kind' instead

    # Metadata
    synonyms: Optional[str] = Field(default=None)  # JSON array of strings
    measurement_ideas: Optional[str] = Field(default=None)  # JSON array of strings
    citations: Optional[str] = Field(default=None)  # JSON array: [{"doc":"d7","span":[1023,1101]}]

    # Position (for UI)
    x: Optional[float] = None
    y: Optional[float] = None


class GraphEdge(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    project_id: int = Field(index=True)
    from_id: str = Field(index=True)
    to_id: str = Field(index=True)

    # Edge type and status
    type: str = Field(default="CAUSES")  # "CAUSES" | "MODERATES" | "MEDIATES" | "CONTRADICTS"
    status: str = Field(default="PROPOSED")  # "PROPOSED" | "ACCEPTED" | "REJECTED"

    # Legacy field (kept for backward compatibility)
    relation: Optional[str] = None  # Deprecated: use 'type' instead

    # Rationale fields (JSON arrays)
    mechanisms: Optional[str] = Field(default=None)  # JSON array of strings
    assumptions: Optional[str] = Field(default=None)  # JSON array of strings
    confounders: Optional[str] = Field(default=None)  # JSON array of strings

    # Evidence
    citations: Optional[str] = Field(default=None)  # JSON array: [{"doc":"d12","span":[220,300],"support":"supports","strength":0.73}]

    # Legacy/supplemental fields
    rationale: Optional[str] = None  # Free-form text
    confidence: Optional[float] = None


# --- NEW: Feedback model ------------------------------------------------------
# Records thumb feedback for either the essay as a whole or an outline item.
# target: "essay" or "outline"
# target_index: outline item index if target == "outline" (else NULL)
# rating: +1 (thumbs up) or -1 (thumbs down)
# comment: optional free text
class Feedback(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    project_id: int = Field(index=True)
    target: str  # "essay" | "outline"
    target_index: Optional[int] = None
    rating: int  # +1 or -1
    comment: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)


# --- LLM Metrics model --------------------------------------------------------
# Tracks LLM API call performance for monitoring and optimization
# prompt_type: "node_extraction" | "edge_rationale" | "composition" | "evidence"
# prompt_version: Version string from prompts/version.py
# latency_ms: Time taken for LLM call in milliseconds
# success: Whether the call completed successfully
# cache_hit: Whether result was served from cache
class LLMMetrics(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    prompt_type: str = Field(index=True)  # For filtering by operation type
    prompt_version: str  # Track performance by prompt version
    latency_ms: int  # Response time in milliseconds
    success: bool  # True if LLM responded, False if error/fallback
    input_tokens: Optional[int] = None  # Tokens in request (if available from provider)
    output_tokens: Optional[int] = None  # Tokens in response (if available from provider)
    cache_hit: bool = False  # True if served from cache
    error_message: Optional[str] = None  # Store error details if failed
    created_at: datetime = Field(default_factory=datetime.utcnow, index=True)  # For time-series analysis
