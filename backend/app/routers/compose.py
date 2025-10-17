# backend/app/routers/compose.py
from __future__ import annotations

from typing import List, Literal, Optional
from fastapi import APIRouter, Response
from pydantic import BaseModel

from ..services import llm  # uses compose_outline_essay + PROVIDER/MODEL

router = APIRouter(prefix="/compose", tags=["compose"])


# ---------- Schemas ----------
class NodeIn(BaseModel):
    id: str
    text: str
    type: Literal["THESIS", "CLAIM"]
    x: Optional[float] = None
    y: Optional[float] = None


class EdgeIn(BaseModel):
    from_id: str
    to_id: str
    relation: Literal["SUPPORTS", "CONTRADICTS"]
    rationale: Optional[str] = None
    confidence: Optional[float] = None


class ComposeIn(BaseModel):
    thesis: Optional[str] = None
    nodes: List[NodeIn]
    edges: List[EdgeIn]
    words: int = 700
    audience: Literal["academic", "general", "policy", "technical"] = "academic"
    tone: Literal["neutral", "critical", "persuasive", "explanatory", "skeptical"] = "neutral"
    mode: Literal["outline", "essay", "both"] = "both"


class OutlineItem(BaseModel):
    heading: str
    points: List[str]


class ComposeOut(BaseModel):
    outline: List[OutlineItem] = []
    essay_md: str = ""


# ---------- Route ----------
@router.post("", response_model=ComposeOut)
def compose(payload: ComposeIn, response: Response):
    """
    Compose outline/essay from selected subgraph.
    - Always returns 200 with a valid body (no 500s).
    - Sets X-LLM-Used: "1" when a real model reply was used (even if salvaged),
      otherwise "0" for deterministic fallback.
    - Sets X-Model so you can see which model was used.
    """
    try:
        data, used = llm.compose_outline_essay(
            thesis=payload.thesis,
            nodes=[n.model_dump() for n in payload.nodes],
            edges=[e.model_dump() for e in payload.edges],
            words=payload.words,
            audience=payload.audience,
            tone=payload.tone,
        )

        response.headers["X-LLM-Used"] = "1" if used else "0"
        response.headers["X-Model"] = f"{llm.PROVIDER}:{llm.MODEL}"

        outline = data.get("outline", [])
        essay_md = data.get("essay_md", "")

        if payload.mode == "outline":
            return ComposeOut(outline=outline, essay_md="")
        if payload.mode == "essay":
            return ComposeOut(outline=[], essay_md=essay_md)
        return ComposeOut(outline=outline, essay_md=essay_md)

    except Exception as e:
        # Never crash the route; provide a small deterministic fallback
        print(f"[/compose] ERROR: {e}")
        response.headers["X-LLM-Used"] = "0"
        response.headers["X-Model"] = f"{llm.PROVIDER}:{llm.MODEL}"

        heading = payload.thesis or "Argument Overview"
        pts = [n.text for n in payload.nodes][:5]
        essay_md = "## " + heading + "\n\n" + "\n\n".join(f"- {p}" for p in pts if p)
        return ComposeOut(outline=[OutlineItem(heading=heading, points=pts)], essay_md=essay_md)


# Alias route used by the frontend: /compose/subgraph
@router.post("/subgraph", response_model=ComposeOut)
def compose_subgraph(payload: ComposeIn, response: Response):
    return compose(payload, response)