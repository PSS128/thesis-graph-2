# backend/app/routers/edge.py
from __future__ import annotations

from typing import List, Literal, Optional, Dict, Any
from fastapi import APIRouter, Response
from pydantic import BaseModel, Field

from ..services.llm import chat_json
from ..services.embeddings import retrieve


#
# Router: edge operations
# - POST /edge/rationale: reason card for A -> B (mechanisms, assumptions, confounders, evidence types)
# - POST /edge/evidence: RAG citations for a confirmed edge
#
router = APIRouter(prefix="/edge", tags=["edge"])


# ---------- Schemas ----------
class RationaleIn(BaseModel):
    a_name: str = Field(..., description="Source variable name (A)")
    b_name: str = Field(..., description="Target variable name (B)")


class RationaleOut(BaseModel):
    mechanisms: List[str] = []
    assumptions: List[str] = []
    likely_confounders: List[str] = []
    prior_evidence_types: List[str] = []


@router.post("/rationale", response_model=RationaleOut)
def edge_rationale(req: RationaleIn) -> RationaleOut:
    """
    On draw A -> B, return a compact reason card.
    """
    system = (
        "You analyze a proposed causal edge A -> B and list mechanisms, assumptions, confounders, and prior evidence types. "
        "Return STRICT JSON ONLY: {\"mechanisms\":[],\"assumptions\":[],\"likely_confounders\":[],\"prior_evidence_types\":[]}."
    )
    user = f"""
User proposes causality A -> B.
A: {req.a_name}
B: {req.b_name}

Return JSON ONLY:
{{
  "mechanisms": ["..."],
  "assumptions": ["..."],
  "likely_confounders": ["..."],
  "prior_evidence_types": ["..."]
}}
""".strip()

    data: Optional[Dict[str, Any]] = chat_json(system, user, temperature=0.2, max_tokens=900)
    if not data:
        return RationaleOut(
            mechanisms=["plausible pathway"],
            assumptions=["ceteris paribus"],
            likely_confounders=["baseline differences"],
            prior_evidence_types=["observational", "experimental"],
        )

    return RationaleOut(
        mechanisms=[s for s in (data.get("mechanisms") or []) if str(s).strip()][:8],
        assumptions=[s for s in (data.get("assumptions") or []) if str(s).strip()][:8],
        likely_confounders=[s for s in (data.get("likely_confounders") or []) if str(s).strip()][:8],
        prior_evidence_types=[s for s in (data.get("prior_evidence_types") or []) if str(s).strip()][:8],
    )


# ---------- Evidence ----------
class EvidenceIn(BaseModel):
    a_name: str
    b_name: str
    mechanisms: Optional[List[str]] = None
    top_k: int = 3


class EvidenceItem(BaseModel):
    title: Optional[str] = None
    url: Optional[str] = None
    quote: str
    span: Optional[List[int]] = None
    supports: Literal["supports", "contradicts"]
    strength: float = 0.0


@router.post("/evidence", response_model=List[EvidenceItem])
def edge_evidence(req: EvidenceIn, response: Response) -> List[EvidenceItem]:
    """
    After edge confirm, run lightweight retrieval over the user's corpus and
    format top passages. This endpoint does not persist; it formats RAG
    results to a stable schema expected by the UI.
    """
    query_parts = [f"Does {req.a_name} cause {req.b_name}?"]
    if req.mechanisms:
        query_parts += ["mechanism: " + m for m in req.mechanisms[:4]]
    query = "; ".join(query_parts)

    hits = retrieve(query, k=max(1, min(6, req.top_k or 3)))
    out: List[EvidenceItem] = []
    for h in hits:
        quote = (h.get("text") or "").strip()
        doc = h.get("doc") or {}
        title = doc.get("title")
        url = doc.get("source")
        strength = float(h.get("score") or 0.0)

        # Heuristic: default to supports unless the snippet contains clear contradict cues.
        label: Literal["supports", "contradicts"] = "supports"
        low = quote.lower()
        if any(w in low for w in ["no effect", "null effect", "contradict", "fail to replicate", "mixed evidence"]):
            label = "contradicts"

        out.append(EvidenceItem(title=title, url=url, quote=quote, span=None, supports=label, strength=strength))

    # Surface provider info in headers for visibility (optional)
    response.headers["X-Model"] = "retrieve:MiniLM-L6-v2"
    return out


