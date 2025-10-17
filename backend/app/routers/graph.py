# backend/app/routers/graph.py
from __future__ import annotations

from typing import List, Literal, Optional, Dict, Any
from fastapi import APIRouter
from pydantic import BaseModel, Field

from ..services.llm import chat_json


#
# Router: graph-level reasoning utilities
# - POST /graph/suggest_mediators
# - POST /graph/critique
#
router = APIRouter(prefix="/graph", tags=["graph"])


# ---------- Schemas ----------
class Node(BaseModel):
    id: str
    name: str
    kind: Literal["THESIS", "VARIABLE", "ASSUMPTION"] = "VARIABLE"


class Edge(BaseModel):
    id: str
    from_id: str
    to_id: str
    type: Literal["CAUSES", "MODERATES", "MEDIATES", "CONTRADICTS"] = "CAUSES"
    status: Literal["PROPOSED", "ACCEPTED", "REJECTED"] = "ACCEPTED"


class MediatorSuggestIn(BaseModel):
    focus_node_id: Optional[str] = Field(None, description="Center node id (optional context)")
    nodes: List[Node]
    edges: List[Edge]


class MediatorSuggestOut(BaseModel):
    mediators: List[str] = []
    moderators: List[str] = []
    study_designs: List[str] = []


@router.post("/suggest_mediators", response_model=MediatorSuggestOut)
def suggest_mediators(req: MediatorSuggestIn) -> MediatorSuggestOut:
    system = (
        "Given a local causal graph, suggest mediators (A -> M -> B), moderators, and feasible study designs. "
        "Return STRICT JSON ONLY: {\"mediators\":[],\"moderators\":[],\"study_designs\":[]}."
    )
    node_lines = "\n".join(f"- {n.id}: {n.name} ({n.kind})" for n in req.nodes)
    edge_lines = "\n".join(f"- {e.id}: {e.from_id} -> {e.to_id} [{e.type}|{e.status}]" for e in req.edges)
    user = f"""
Nodes:\n{node_lines}\n\nEdges:\n{edge_lines}\n\nFocus: {req.focus_node_id or "(none)"}
Return strict JSON with mediators, moderators, and study_designs.
""".strip()

    data = chat_json(system, user, temperature=0.3, max_tokens=900)
    if not data:
        return MediatorSuggestOut(
            mediators=["intermediate process"],
            moderators=["contextual factor"],
            study_designs=["difference-in-differences", "randomized controlled trial"],
        )
    return MediatorSuggestOut(
        mediators=[s for s in (data.get("mediators") or []) if str(s).strip()][:8],
        moderators=[s for s in (data.get("moderators") or []) if str(s).strip()][:8],
        study_designs=[s for s in (data.get("study_designs") or []) if str(s).strip()][:8],
    )


# ---------- Critique ----------
class CritiqueIn(BaseModel):
    nodes: List[Node]
    edges: List[Edge]


class WarningItem(BaseModel):
    node_or_edge_id: str
    label: str
    fix_suggestion: str


class CritiqueOut(BaseModel):
    warnings: List[WarningItem] = []


@router.post("/critique", response_model=CritiqueOut)
def critique_graph(req: CritiqueIn) -> CritiqueOut:
    system = (
        "You are a DAG checker. Detect: confounding not adjusted, collider/mediator misuse, and edges with no evidence. "
        "Return JSON ONLY: {\"warnings\":[{\"node_or_edge_id\":\"...\",\"label\":\"...\",\"fix_suggestion\":\"...\"}]}"
    )
    node_lines = "\n".join(f"- {n.id}: {n.name} ({n.kind})" for n in req.nodes)
    edge_lines = "\n".join(f"- {e.id}: {e.from_id}->{e.to_id} [{e.type}|{e.status}]" for e in req.edges)
    user = f"""
Nodes:\n{node_lines}\n\nEdges:\n{edge_lines}\n\nInstructions:\n- Flag confounding not adjusted (missing back-door set).
- Warn on conditioning on colliders or blocking mediators when estimating total effects.
- Mark edges with no evidence (no citations) if apparent from context.
Return strict JSON with warnings.
""".strip()

    data = chat_json(system, user, temperature=0.2, max_tokens=900)
    warnings = []
    if data and isinstance(data.get("warnings"), list):
        for w in data["warnings"]:
            nid = str(w.get("node_or_edge_id") or "").strip()
            lbl = str(w.get("label") or "").strip()
            fix = str(w.get("fix_suggestion") or "").strip()
            if nid and lbl:
                warnings.append(WarningItem(node_or_edge_id=nid, label=lbl, fix_suggestion=fix or "Review model specification."))

    return CritiqueOut(warnings=warnings[:16])


