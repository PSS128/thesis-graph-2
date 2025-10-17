# backend/app/routers/extract.py
from __future__ import annotations

import re
from typing import List, Optional, Literal
from fastapi import APIRouter
from pydantic import BaseModel

# Use our robust chat_json helper
from ..services.llm import chat_json

router = APIRouter(prefix="/extract", tags=["extract"])

NodeType = Literal["THESIS", "CLAIM"]


# ---------- Schemas ----------
class ExtractRequest(BaseModel):
    text: str
    thesis: Optional[str] = None
    max_items: int = 8


class NodeOut(BaseModel):
    id: str
    text: str
    type: NodeType


# ---------- Fallback (no LLM) ----------
def _fallback_extract(text: str, thesis: Optional[str], max_items: int) -> List[NodeOut]:
    nodes: List[NodeOut] = []
    idx = 1

    if thesis:
        nodes.append(NodeOut(id=f"n{idx}", type="THESIS", text=thesis.strip()))
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
        nodes.append(NodeOut(id=f"n{idx}", type="CLAIM", text=s2))
        idx += 1
        if len(nodes) >= max_items:
            break
    return nodes[:max_items]


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
        if not _text or _type not in ("THESIS", "CLAIM"):
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


# ---------- Route ----------
@router.post("/nodes", response_model=List[NodeOut])
def extract_nodes(req: ExtractRequest):
    print("[/extract/nodes] incoming", len(req.text or ""), "chars", "thesis?", bool(req.thesis))

    max_items = max(1, min(16, req.max_items or 8))

    system = (
        "You extract atomic, self-contained claims from a passage. "
        "Return STRICT JSON ONLY. No prose, no code fences."
    )
    user = f"""
Text:
{req.text}

Thesis (optional):
{req.thesis or ""}

Instructions:
- Extract up to {max_items} items.
- If a thesis is provided, include exactly one node of type "THESIS" using that thesis text.
- All other nodes must be type "CLAIM".
- Create compact, non-overlapping statements.
- Use ids 'n1','n2',... in order.

Return strict JSON (no extra keys):
{{
  "nodes":[
    {{"id":"n1","type":"THESIS","text":"..."}},
    {{"id":"n2","type":"CLAIM","text":"..."}}
  ]
}}
""".strip()

    data = chat_json(system, user)

    # If model returned something, try to normalize/repair
    if data and isinstance(data.get("nodes"), list):
        normalized = _normalize_nodes(data["nodes"], req.thesis, max_items)
        if normalized:
            return normalized

    # Fallback (deterministic)
    return _fallback_extract(req.text, req.thesis, max_items)
