# backend/app/routers/node.py
from __future__ import annotations

from typing import List, Optional, Dict, Any
from fastapi import APIRouter
from pydantic import BaseModel, Field

# Centralized LLM helper (JSON coercion, provider badges)
from ..services.llm import chat_json


#
# Router: node-centric operations (singular prefix to match frontend hooks)
# - POST /node/extract: map a highlighted sentence into a canonical variable
#   with concise name, short definition, synonyms, and measurement ideas.
#
router = APIRouter(prefix="/node", tags=["node"])


# ---------- Schemas ----------
class ExtractVariableIn(BaseModel):
    text: str = Field(..., description="Highlighted text from PDF/web page")
    source_ref: Optional[str] = Field(None, description="Opaque source reference (doc id, url, etc.)")
    # Optional: existing node names to enable merge hints (client may pass subset)
    existing_names: Optional[List[str]] = Field(None, description="Known node names for similarity/merge suggestions")


class MergeHint(BaseModel):
    existing_name: str
    similarity: float
    action: str = Field("merge_or_keep", description="UI hint label; not enforced server-side")


class ExtractVariableOut(BaseModel):
    name: str
    definition: str
    synonyms: List[str] = []
    measurement_ideas: List[str] = []
    merge_hint: Optional[MergeHint] = None


# ---------- Route ----------
@router.post("/extract", response_model=ExtractVariableOut)
def extract_variable(req: ExtractVariableIn) -> ExtractVariableOut:
    """
    Convert a highlighted sentence into a canonical causal variable descriptor.

    Contract expected by the frontend:
      Returns JSON: {name, definition, synonyms[], measurement_ideas[]}
      Optionally returns a merge_hint when an existing name is very similar.

    Behavior:
      - Tries LLM JSON mode via chat_json to structure the response.
      - Adds a pragmatic, deterministic fallback if the LLM is unavailable.
      - Performs a lightweight string-similarity pass for merge hints when
        existing_names are provided by the client (no DB dependency needed).
    """

    # System instruction tightly constrains the format and style
    system = (
        "You map a highlighted sentence to a SINGLE causal variable. "
        "Return STRICT JSON ONLY as {\"name\",\"definition\",\"synonyms\",\"measurement_ideas\"}. "
        "Keep the name concise and domain-neutral."
    )

    user = f"""
Text (highlight):
{req.text}

Instructions:
- Propose a single canonical variable name.
- Provide a one-sentence definition.
- Include 2-6 concise synonyms.
- Include 2-6 concrete measurement ideas.

Return JSON ONLY:
{{
  "name": "...",
  "definition": "...",
  "synonyms": ["..."],
  "measurement_ideas": ["..."]
}}
""".strip()

    data: Optional[Dict[str, Any]] = chat_json(system, user, temperature=0.2, max_tokens=800)

    # Guard: produce a deterministic fallback if model is unavailable
    if not data or not isinstance(data, dict):
        base = ExtractVariableOut(
            name="Candidate Variable",
            definition="A concise causal factor inferred from the highlight.",
            synonyms=["factor", "predictor"],
            measurement_ideas=["expert rating", "survey scale"],
        )
        return _with_merge_hint(base, req.existing_names)

    # Normalize fields defensively (robust to partial model outputs)
    name = (str(data.get("name") or "").strip()) or "Candidate Variable"
    definition = (str(data.get("definition") or "").strip()) or "A concise causal factor."
    synonyms = [str(s).strip() for s in (data.get("synonyms") or []) if str(s).strip()]
    measurement = [str(m).strip() for m in (data.get("measurement_ideas") or []) if str(m).strip()]

    out = ExtractVariableOut(
        name=name,
        definition=definition,
        synonyms=synonyms[:8],
        measurement_ideas=measurement[:8],
    )
    return _with_merge_hint(out, req.existing_names)


# ---------- Helpers ----------
def _with_merge_hint(out: ExtractVariableOut, existing: Optional[List[str]]) -> ExtractVariableOut:
    """
    If the client provided existing_names, compute a simple similarity and
    attach a merge_hint when a close match is found. The goal is UI guidance,
    not de-duplication logic (the client remains the source of truth).
    """
    if not existing:
        return out

    best_name = None
    best_score = 0.0
    for name in existing:
        score = _soft_similarity(out.name, name)
        if score > best_score:
            best_name = name
            best_score = score

    if best_name and best_score >= 0.75:
        out.merge_hint = MergeHint(existing_name=best_name, similarity=round(best_score, 3))
    return out


def _soft_similarity(a: str, b: str) -> float:
    """
    Lightweight token Jaccard similarity (case/space/sep normalized).
    Good enough for a hint without adding dependencies.
    """
    ta = {t for t in _tokenize(a)}
    tb = {t for t in _tokenize(b)}
    if not ta or not tb:
        return 0.0
    inter = len(ta & tb)
    union = len(ta | tb)
    return inter / union if union else 0.0


def _tokenize(s: str) -> List[str]:
    return [t for t in (
        s.lower().replace("-", " ").replace("_", " ").replace("/", " ").split()
    ) if t]


