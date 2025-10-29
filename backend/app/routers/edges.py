# backend/app/routers/edges.py
from __future__ import annotations

from typing import List, Literal
import itertools
import re

from fastapi import APIRouter
from pydantic import BaseModel

from ..services.llm import chat_json

router = APIRouter(prefix="/edges", tags=["edges"])

Relation = Literal["SUPPORTS", "CONTRADICTS", "DEFINES"]


# ---------- Schemas ----------
class NodeIn(BaseModel):
    id: str
    text: str
    type: Literal["THESIS", "CLAIM", "EVIDENCE", "VARIABLE"]


class EdgeOut(BaseModel):
    from_id: str
    to_id: str
    relation: Relation
    # keep the output minimal; rationale/confidence can be added later if you like


class SuggestRequest(BaseModel):
    nodes: List[NodeIn]
    max_edges: int = 12


# ---------- Fallback heuristic (no LLM) ----------
NEG_WORDS = {
    "not",
    "no",
    "never",
    "cannot",
    "can't",
    "won't",
    "n't",
    "however",
    "but",
    "contradict",
    "versus",
    "oppose",
}


def _looks_contradict(a: str, b: str) -> bool:
    text = f"{(a or '').lower()} {(b or '').lower()}"
    return any(w in text for w in NEG_WORDS)


def _fallback_suggest(nodes: List[NodeIn], max_edges: int) -> List[EdgeOut]:
    """Naive pairwise: CONTRADICTS if negation/contrast appears; else SUPPORTS."""
    out: List[EdgeOut] = []
    for n1, n2 in itertools.combinations(nodes, 2):
        if len(out) >= max_edges:
            break
        rel: Relation = "CONTRADICTS" if _looks_contradict(n1.text, n2.text) else "SUPPORTS"
        out.append(EdgeOut(from_id=n1.id, to_id=n2.id, relation=rel))
    return out[:max_edges]


# ---------- LLM prompt ----------
def _llm_edges_prompt(nodes: List[NodeIn], max_edges: int) -> tuple[str, str]:
    system = (
        "You are linking claims into a small argument graph. "
        "Return STRICT JSON ONLY. Only include defensible edges."
    )

    lines = []
    for n in nodes:
        t = re.sub(r"\s+", " ", (n.text or "")).strip()
        lines.append(f"- {n.id} [{n.type}]: {t}")

    user = f"""
Claims:
{chr(10).join(lines)}

Instructions:
- Propose up to {max_edges} edges.
- Use only ids provided.
- Relation must be one of: "SUPPORTS", "CONTRADICTS", or "DEFINES".
- "SUPPORTS": Evidence supports a claim, or a claim supports thesis
- "CONTRADICTS": Claims that contradict each other
- "DEFINES": Evidence that defines or measures a variable
- Prefer clear, high-confidence links.
- Do NOT include self-loops or duplicate edges.

Return strict JSON (no extra keys):
{{
  "edges": [
    {{"from_id":"n2","to_id":"n5","relation":"SUPPORTS"}},
    {{"from_id":"n3","to_id":"n1","relation":"CONTRADICTS"}},
    {{"from_id":"n4","to_id":"n6","relation":"DEFINES"}}
  ]
}}
""".strip()

    return system, user


# ---------- Route ----------
@router.post("/suggest", response_model=List[EdgeOut])
def suggest_edges(req: SuggestRequest):
    print("[/edges/suggest] nodes:", len(req.nodes), "max:", req.max_edges)

    max_edges = max(1, min(32, req.max_edges or 12))
    nodes = req.nodes or []
    if len(nodes) < 2:
        return []

    id_set = {n.id for n in nodes}

    # Try LLM first
    system, user = _llm_edges_prompt(nodes, max_edges)
    data = chat_json(system, user)

    if data and isinstance(data.get("edges"), list):
        out: List[EdgeOut] = []
        for e in data["edges"]:
            a = (e.get("from_id") or "").strip()
            b = (e.get("to_id") or "").strip()
            rel = (e.get("relation") or "").strip().upper()
            if not a or not b or a == b or a not in id_set or b not in id_set:
                continue
            if rel not in ("SUPPORTS", "CONTRADICTS", "DEFINES"):
                continue
            out.append(EdgeOut(from_id=a, to_id=b, relation=rel))  # type: ignore

        if out:
            # De-dup directed edges and cap
            seen = set()
            unique: List[EdgeOut] = []
            for e in out:
                key = (e.from_id, e.to_id, e.relation)
                if key in seen:
                    continue
                seen.add(key)
                unique.append(e)
            return unique[:max_edges]

    # Fallback if LLM absent or returned junk
    return _fallback_suggest(nodes, max_edges)
