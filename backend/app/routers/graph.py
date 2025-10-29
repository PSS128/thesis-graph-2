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


class MediatorDetail(BaseModel):
    name: str
    definition: str
    rationale: str


class ModeratorDetail(BaseModel):
    name: str
    definition: str
    rationale: str


class MeasurementIdea(BaseModel):
    approach: str
    description: str
    pros: List[str]
    cons: List[str]


class ConfounderDetail(BaseModel):
    name: str
    definition: str
    rationale: str


class MissingPiecesOut(BaseModel):
    mediators: List[MediatorDetail] = []
    moderators: List[ModeratorDetail] = []
    measurements: List[MeasurementIdea] = []
    confounders: List[ConfounderDetail] = []


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


@router.post("/missing_pieces", response_model=MissingPiecesOut)
def missing_pieces(req: MediatorSuggestIn) -> MissingPiecesOut:
    """
    Enhanced endpoint that provides detailed suggestions with definitions and rationales.
    """
    # Find the focus node if specified
    focus_node = None
    if req.focus_node_id:
        focus_node = next((n for n in req.nodes if n.id == req.focus_node_id), None)

    focus_name = focus_node.name if focus_node else "the graph"

    system = (
        "You are both a causal inference expert and a critical reviewer."
        "Your job is to analyze, challenge, and strengthen the causal reasoning in my argument, essay, or analysis."
        "Primary Goals:"

        "Identify where causal relationships are weak, assumed, or ambiguous."
        "Suggest specific measurable variables and data collection methods that could support or falsify the claims."
        "Detect logical fallacies, confounding factors, omitted variables, or reverse causality risks."
        "Reframe vague claims into testable hypotheses that could withstand scrutiny from a skeptical expert audience."        
        "Return STRICT JSON ONLY. No prose, no code fences."
    )

    node_lines = "\n".join(f"- {n.name} ({n.kind})" for n in req.nodes)
    edge_lines = "\n".join(f"- {e.from_id} → {e.to_id} ({e.type})" for e in req.edges)

    user = f"""
Analyze this causal graph and suggest missing pieces:

Focus variable: {focus_name}

Current variables:
{node_lines}

Current relationships:
{edge_lines}

Provide:
1. MEDIATORS - variables that might sit on causal paths
2. MODERATORS - conditions that strengthen/weaken effects
3. MEASUREMENTS - concrete ways to operationalize variables
4. CONFOUNDERS - variables that might bias relationships

Return JSON:
{{
  "mediators": [
    {{"name": "specific variable name", "definition": "clear definition", "rationale": "why this mediates"}}
  ],
  "moderators": [
    {{"name": "specific condition", "definition": "clear definition", "rationale": "how this moderates"}}
  ],
  "measurements": [
    {{"approach": "measurement method", "description": "how to measure", "pros": ["pro1"], "cons": ["con1"]}}
  ],
  "confounders": [
    {{"name": "confounder variable", "definition": "clear definition", "rationale": "why this confounds"}}
  ]
}}

Provide 2-3 suggestions per category. Be specific and actionable.
""".strip()

    data = chat_json(system, user, temperature=0.3, max_tokens=1500)

    if not data or not isinstance(data, dict):
        return MissingPiecesOut()

    # Parse mediators
    mediators = []
    for m in (data.get("mediators") or [])[:3]:
        if isinstance(m, dict) and m.get("name"):
            mediators.append(MediatorDetail(
                name=str(m.get("name", "")),
                definition=str(m.get("definition", "")),
                rationale=str(m.get("rationale", ""))
            ))

    # Parse moderators
    moderators = []
    for m in (data.get("moderators") or [])[:3]:
        if isinstance(m, dict) and m.get("name"):
            moderators.append(ModeratorDetail(
                name=str(m.get("name", "")),
                definition=str(m.get("definition", "")),
                rationale=str(m.get("rationale", ""))
            ))

    # Parse measurements
    measurements = []
    for m in (data.get("measurements") or [])[:3]:
        if isinstance(m, dict) and m.get("approach"):
            pros = m.get("pros", [])
            cons = m.get("cons", [])
            measurements.append(MeasurementIdea(
                approach=str(m.get("approach", "")),
                description=str(m.get("description", "")),
                pros=[str(p) for p in pros] if isinstance(pros, list) else [],
                cons=[str(c) for c in cons] if isinstance(cons, list) else []
            ))

    # Parse confounders
    confounders = []
    for c in (data.get("confounders") or [])[:3]:
        if isinstance(c, dict) and c.get("name"):
            confounders.append(ConfounderDetail(
                name=str(c.get("name", "")),
                definition=str(c.get("definition", "")),
                rationale=str(c.get("rationale", ""))
            ))

    return MissingPiecesOut(
        mediators=mediators,
        moderators=moderators,
        measurements=measurements,
        confounders=confounders
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



