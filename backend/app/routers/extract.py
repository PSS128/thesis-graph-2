# backend/app/routers/extract.py
from __future__ import annotations

import re
from typing import List, Optional, Literal
from fastapi import APIRouter
from pydantic import BaseModel

# Use our robust chat_json helper
from ..services.llm import chat_json

router = APIRouter(prefix="/extract", tags=["extract"])

NodeType = Literal["THESIS", "CLAIM", "EVIDENCE", "VARIABLE"]


# ---------- Schemas ----------
class ExtractRequest(BaseModel):
    text: str
    thesis: Optional[str] = None
    max_items: int = 8


class NodeOut(BaseModel):
    id: str
    text: str
    type: NodeType


class EdgeOut(BaseModel):
    from_id: str
    to_id: str
    relation: str  # "SUPPORTS", "DEFINES", etc.


class ExtractResponse(BaseModel):
    nodes: List[NodeOut]
    edges: List[EdgeOut]


# ---------- Fallback (no LLM) ----------
def _fallback_extract(text: str, thesis: Optional[str], max_items: int) -> ExtractResponse:
    nodes: List[NodeOut] = []
    edges: List[EdgeOut] = []
    idx = 1

    thesis_id = None
    if thesis:
        thesis_id = f"n{idx}"
        nodes.append(NodeOut(id=thesis_id, type="THESIS", text=thesis.strip()))
        idx += 1

    # naive sentence split
    sents = re.split(r"(?<=[.!?])\s+", text or "")
    seen_texts = set()
    for s in sents:
        s2 = " ".join((s or "").strip().split())
        if len(s2) < 5:
            continue
        k = s2.lower()
        if k in seen_texts:
            continue
        seen_texts.add(k)
        claim_id = f"n{idx}"
        nodes.append(NodeOut(id=claim_id, type="CLAIM", text=s2))

        # If thesis exists, connect claims to it
        if thesis_id:
            edges.append(EdgeOut(from_id=claim_id, to_id=thesis_id, relation="SUPPORTS"))

        idx += 1
        if len(nodes) >= max_items:
            break

    return ExtractResponse(nodes=nodes[:max_items], edges=edges)


# ---------- Helpers ----------
_id_re = re.compile(r"^n\d+$", re.IGNORECASE)


def _normalize_nodes(
    raw_nodes: List[dict],
    thesis_text: Optional[str],
    max_items: int,
) -> List[NodeOut]:
    """
    Validate & coerce model output into clean NodeOut[]:
      - one THESIS max (prefer explicit thesis param)
      - ids are unique; repair invalid/duplicate ids to n1..nK
      - trim whitespace; drop empties
      - de-duplicate by (type,text) case-insensitively
      - supports THESIS, CLAIM, EVIDENCE, VARIABLE types
    """
    out: List[NodeOut] = []
    seen_text_type = set()
    next_idx = 1

    def next_id() -> str:
        nonlocal next_idx
        nid = f"n{next_idx}"
        next_idx += 1
        return nid

    # If user provided thesis, pin it as the first node
    thesis_added = False
    if thesis_text and thesis_text.strip():
        out.append(NodeOut(id=next_id(), type="THESIS", text=thesis_text.strip()))
        thesis_added = True

    # Walk model candidates
    for n in raw_nodes or []:
        if len(out) >= max_items:
            break
        _text = (n.get("text") or "").strip()
        _type = (n.get("type") or "CLAIM").strip().upper()
        if not _text or _type not in ("THESIS", "CLAIM", "EVIDENCE", "VARIABLE"):
            continue

        # Enforce single THESIS
        if _type == "THESIS" and thesis_added:
            continue

        # de-dup on (type,text)
        key = (_type, _text.lower())
        if key in seen_text_type:
            continue
        seen_text_type.add(key)

        # repair/assign id
        nid = (n.get("id") or "").strip()
        if not _id_re.match(nid) or any(existing.id == nid for existing in out):
            nid = next_id()

        out.append(NodeOut(id=nid, type=_type, text=_text))
        if _type == "THESIS":
            thesis_added = True

    # If still no nodes, return []
    return out[:max_items]


def _normalize_edges(
    raw_edges: List[dict],
    valid_node_ids: set[str],
) -> List[EdgeOut]:
    """
    Validate & clean edges:
      - both from_id and to_id must exist in valid_node_ids
      - trim whitespace; drop invalid
      - de-duplicate
    """
    out: List[EdgeOut] = []
    seen_edges = set()

    for e in raw_edges or []:
        from_id = (e.get("from_id") or "").strip()
        to_id = (e.get("to_id") or "").strip()
        relation = (e.get("relation") or "SUPPORTS").strip().upper()

        # Validate node IDs exist
        if not from_id or not to_id:
            continue
        if from_id not in valid_node_ids or to_id not in valid_node_ids:
            continue

        # De-duplicate edges
        edge_key = (from_id, to_id, relation)
        if edge_key in seen_edges:
            continue
        seen_edges.add(edge_key)

        out.append(EdgeOut(from_id=from_id, to_id=to_id, relation=relation))

    return out


# ---------- Route ----------
@router.post("/nodes", response_model=ExtractResponse)
def extract_nodes(req: ExtractRequest):
    print("[/extract/nodes] incoming", len(req.text or ""), "chars", "thesis?", bool(req.thesis))

    max_items = max(1, min(16, req.max_items or 8))

    system = (
        "You are an information extraction model specializing in factual claim extraction. "
        "Your task is to extract atomic, self-contained, verifiable claims, evidence, and variables from the given passage. "

        "Node Types: "
        "- CLAIM: A short, declarative statement that asserts something that can be evaluated as true or false. "
        "- EVIDENCE: Specific data, quotes, statistics, or observations from the text that support a claim. "
        "- VARIABLE: A measurable or observable concept mentioned in the text (e.g., 'GDP growth', 'temperature', 'customer satisfaction'). "
        "- THESIS: The main argument or position (if provided). "

        "Follow these strict principles: "

        "Verifiability – Include only factual content that could be checked against external evidence. "
        "Exclude opinions, recommendations, or normative statements (e.g., \"should,\" \"must,\" \"important,\" \"requires\"). "

        "Entailment – Each claim must be fully supported by the source text. "
        "Do not infer unstated details, merge facts from multiple sentences, or generalize beyond what is explicitly said. "

        "Self-containment – Each claim must be understandable on its own, without needing additional context or references like \"they,\" \"this,\" or \"those.\" "
        "Rewrite pronouns or vague terms to specify what they refer to. "

        "Context preservation – Include all qualifiers or conditions that are critical for accurate interpretation. "
        "For example, instead of \"The WTO has supported trade barriers,\" write \"The WTO has supported trade barriers when member countries failed to comply with obligations.\" "

        "Evidence extraction – For each claim, identify specific evidence from the text that supports it. "
        "Evidence should be direct quotes, data points, or specific observations from the source. "

        "Variable identification – Extract measurable concepts or variables mentioned in the text and connect them to their supporting evidence. "

        "Connections – Create edges that show relationships: "
        "- SUPPORTS: Evidence supports a claim, or a claim supports the thesis. "
        "- DEFINES: Evidence defines or measures a variable. "

        "Completeness – Capture all verifiable information present in the text. "
        "Avoid omitting causation, magnitude, or temporal qualifiers that change meaning. "

        "Return output in STRICT JSON ONLY — no prose, no code fences."
    )
    user = f"""
Text:
{req.text}

Thesis (optional):
{req.thesis or ""}

Instructions:
- Extract up to {max_items} items total (claims + evidence + variables).
- If a thesis is provided, include exactly one node of type "THESIS" using that thesis text.
- Extract CLAIM nodes for main assertions.
- Extract EVIDENCE nodes for data, quotes, or specific facts that support claims.
- Extract VARIABLE nodes for measurable concepts mentioned in the text.
- Create edges to connect evidence to claims (SUPPORTS) and evidence to variables (DEFINES).
- Use ids 'n1','n2','n3'... for nodes in order.
- Create compact, non-overlapping statements.

Return strict JSON (no extra keys):
{{
  "nodes":[
    {{"id":"n1","type":"THESIS","text":"..."}},
    {{"id":"n2","type":"CLAIM","text":"..."}},
    {{"id":"n3","type":"EVIDENCE","text":"..."}},
    {{"id":"n4","type":"VARIABLE","text":"..."}}
  ],
  "edges":[
    {{"from_id":"n3","to_id":"n2","relation":"SUPPORTS"}},
    {{"from_id":"n3","to_id":"n4","relation":"DEFINES"}}
  ]
}}
""".strip()

    data = chat_json(system, user)

    # If model returned something, try to normalize/repair
    if data and isinstance(data.get("nodes"), list):
        normalized_nodes = _normalize_nodes(data["nodes"], req.thesis, max_items)
        if normalized_nodes:
            # Get valid node IDs
            valid_ids = {n.id for n in normalized_nodes}
            # Normalize edges
            normalized_edges = _normalize_edges(data.get("edges", []), valid_ids)
            return ExtractResponse(nodes=normalized_nodes, edges=normalized_edges)

    # Fallback (deterministic)
    return _fallback_extract(req.text, req.thesis, max_items)
