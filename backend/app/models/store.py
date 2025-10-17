# backend/app/models/store.py
from __future__ import annotations

from datetime import datetime
from typing import Optional
from sqlmodel import SQLModel, Field


class Project(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    title: str


class GraphNode(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    project_id: int = Field(index=True)
    node_id: str = Field(index=True)
    text: str
    type: str  # "THESIS" | "CLAIM"
    x: Optional[float] = None
    y: Optional[float] = None


class GraphEdge(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    project_id: int = Field(index=True)
    from_id: str
    to_id: str
    relation: str  # "SUPPORTS" | "CONTRADICTS"
    rationale: Optional[str] = None
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
