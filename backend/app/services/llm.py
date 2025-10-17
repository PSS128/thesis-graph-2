# backend/app/services/llm.py
"""
Unified LLM service layer for the Thesis Graph app.
Supports OpenAI or Groq. Robust JSON handling for extract/edges/compose.

Exports:
- provider_info(), ping()
- chat_once(system, user, ...)
- chat_json(system, user, ...)              # strict JSON helper for extract/edges
- compose_outline_essay(thesis, nodes, ...) # -> ({"outline":[...],"essay_md":"..."}, used_bool)
"""

from __future__ import annotations
import os
from dotenv import load_dotenv
import json
import re
from typing import Any, Dict, List, Optional, Tuple
load_dotenv()

# --- API keys ---
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

# ------------------------------------------------------------------
# Provider config (env-driven)
# ------------------------------------------------------------------
PROVIDER = os.getenv("LLM_PROVIDER", "groq").lower()   # "groq" | "openai"
MODEL    = os.getenv("LLM_MODEL", "llama-3.1-8b-instant")

# Try to import both SDKs; we'll only use the selected one.
try:
    from groq import Groq
except Exception:
    Groq = None

try:
    from openai import OpenAI
except Exception:
    OpenAI = None


def _client():
    """Return active SDK client or None if not configured."""
    if PROVIDER == "groq" and Groq and os.getenv("GROQ_API_KEY"):
        return Groq(api_key=os.getenv("GROQ_API_KEY"))
    if PROVIDER == "openai" and OpenAI and os.getenv("OPENAI_API_KEY"):
        return OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    return None


# ------------------------------------------------------------------
# Low-level chat helper
# ------------------------------------------------------------------
def _chat(
    system_prompt: str,
    user_prompt: str,
    temperature: float = 0.7,
    max_tokens: int = 1500,
    json_mode: bool = False,
) -> Tuple[str, bool]:
    """
    Attempt a single chat completion. Returns (text, used_llm).
    If no creds/SDK or the call fails, returns a fallback string and used=False.

    json_mode=True:
      - For OpenAI, uses response_format={"type":"json_object"}.
      - For Groq, we just rely on instructions; there's no server-side JSON mode.
    """
    client = _client()
    if not client:
        return "[LLM unavailable — using fallback response.]", False

    try:
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user",   "content": user_prompt},
        ]

        # Build provider-specific kwargs
        kwargs: Dict[str, Any] = dict(model=MODEL, temperature=temperature, messages=messages)

        if PROVIDER == "openai":
            # OpenAI chat.completions uses max_completion_tokens (v1 SDK)
            kwargs["max_completion_tokens"] = max_tokens
            if json_mode:
                kwargs["response_format"] = {"type": "json_object"}
        else:
            # Groq uses max_tokens
            kwargs["max_tokens"] = max_tokens

        result = client.chat.completions.create(**kwargs)
        text = (result.choices[0].message.content or "").strip()
        return text, True

    except Exception as e:
        print(f"[LLM ERROR] {_safe(e)}")
        return f"[Error invoking LLM: {_safe(e)}]", False


# ------------------------------------------------------------------
# JSON helpers
# ------------------------------------------------------------------
_CODE_FENCE_RE = re.compile(r"^```(?:json)?\s*|\s*```$", re.IGNORECASE | re.MULTILINE)
_TRAILING_COMMAS_RE = re.compile(r",(\s*[}\]])")

def _strip_code_fences(s: str) -> str:
    # Remove ```json ... ``` wrappers
    return _CODE_FENCE_RE.sub("", s).strip()

def _normalize_quotes(s: str) -> str:
    # Replace smart quotes with plain quotes
    return (s.replace("\u201c", '"')
             .replace("\u201d", '"')
             .replace("\u2018", "'")
             .replace("\u2019", "'"))

def _relaxed_json_fixups(s: str) -> str:
    # Remove trailing commas before } or ]
    s = _TRAILING_COMMAS_RE.sub(r"\1", s)
    # If the model used single quotes consistently, try a cautious swap.
    # (We do NOT try to be perfect; just a pragmatic fix.)
    if '"' not in s and "'" in s:
        s = s.replace("'", '"')
    return s

def _extract_json_strict(text: str) -> Optional[Dict[str, Any]]:
    """Extract the largest {...} block and json.loads it."""
    if not text:
        return None
    s = _strip_code_fences(_normalize_quotes(text))
    start = s.find("{")
    end   = s.rfind("}")
    if start == -1 or end == -1 or end <= start:
        return None
    try:
        return json.loads(s[start:end+1])
    except Exception:
        return None

def _extract_json_relaxed(text: str) -> Optional[Dict[str, Any]]:
    """Try again with relaxed fixups (trailing commas, single quotes)."""
    if not text:
        return None
    s = _strip_code_fences(_normalize_quotes(text))
    start = s.find("{")
    end   = s.rfind("}")
    if start == -1 or end == -1 or end <= start:
        return None
    chunk = _relaxed_json_fixups(s[start:end+1])
    try:
        return json.loads(chunk)
    except Exception as e:
        print(f"[JSON PARSE ERROR] {_safe(e)}\nTEXT: {text[:400]}")
        return None


def chat_json(
    system_prompt: str,
    user_prompt: str,
    temperature: float = 0.2,
    max_tokens: int = 1200,
) -> Optional[Dict[str, Any]]:
    """
    Ask for strict JSON and parse it. Returns dict or None.
    Uses OpenAI JSON mode when available to reduce parse failures.
    """
    # Strengthen the instruction regardless of provider.
    sys = (system_prompt or "") + "\nReturn ONLY a single valid JSON object. Start with '{' and end with '}'."
    usr = user_prompt

    text, used = _chat(sys, usr, temperature=temperature, max_tokens=max_tokens, json_mode=True)
    data = _extract_json_strict(text)
    if data is not None:
        return data

    # Second chance with relaxed fixups (helps Groq or non-JSON-mode outputs)
    data = _extract_json_relaxed(text)
    if data is not None:
        return data

    print("[chat_json] model did not return strict JSON; using None fallback.")
    return None


# ------------------------------------------------------------------
# Compose helper
# ------------------------------------------------------------------
def compose_outline_essay(
    thesis: Optional[str],
    nodes: List[Dict[str, Any]],
    edges: List[Dict[str, Any]],
    words: int = 700,
    audience: str = "academic",
    tone: str = "neutral",
) -> Tuple[Dict[str, Any], bool]:
    """
    Produce a structured outline + essay from the selected subgraph.
    Always returns (data_dict, used_bool). Never raises.

    Badge semantics:
      - If the model responded at all, we try to keep used=True, even if we salvage.
      - Only when we never reached a model (no creds/network fail) do we return used=False.
    """
    node_lines = "\n".join(f"- {n.get('text','').strip()}" for n in nodes if n.get("text"))
    system_prompt = (
        "You are a careful reasoning assistant. "
        "Return STRICT JSON ONLY: {\"outline\":[{\"heading\":\"...\",\"points\":[\"...\"]}],"
        "\"essay_md\":\"...\"}. No extra text."
    )
    user_prompt = (
        f"Thesis: {thesis or ''}\n\n"
        f"Claims:\n{node_lines}\n\n"
        f"Audience: {audience}\nTone: {tone}\nTargetWords: {words}\n"
        "Write the outline (3–6 sections) and a concise markdown essay integrating the claims. "
        "Return ONLY the strict JSON object."
    )

    text, used = _chat(system_prompt, user_prompt, temperature=0.5, max_tokens=1800, json_mode=True)

    # Prefer strict JSON
    data = _extract_json_strict(text) or _extract_json_relaxed(text) or {}
    if data.get("outline") and data.get("essay_md"):
        return data, used

    # Salvage the model text if we got any — keep used=True so the badge flips on.
    if used and isinstance(text, str) and text.strip():
        heading = thesis or "Argument Overview"
        pts = [n.get("text", "") for n in nodes][:5]
        outline = [{"heading": heading, "points": [p for p in pts if p]}]
        return {"outline": outline, "essay_md": text}, True

    # True deterministic fallback (no model used)
    heading = thesis or "Argument Overview"
    pts = [n.get("text", "") for n in nodes][:5]
    outline = [{"heading": heading, "points": [p for p in pts if p]}]
    essay_md = f"## {heading}\n\n" + "\n\n".join(f"- {p}" for p in pts if p)
    return {"outline": outline, "essay_md": essay_md}, False


# ------------------------------------------------------------------
# Diagnostics (used by /debug/llm)
# ------------------------------------------------------------------
def provider_info() -> Dict[str, Any]:
    return {
        "provider": PROVIDER,
        "model": MODEL,
        "api_key_present": bool(os.getenv("GROQ_API_KEY") or os.getenv("OPENAI_API_KEY")),
        "sdk_present": bool((PROVIDER == "groq" and Groq) or (PROVIDER == "openai" and OpenAI)),
        "ok": _client() is not None,
    }

def ping() -> Dict[str, Any]:
    """
    Lightweight round-trip check for /debug/llm.
    Returns { ok, provider, model, api_key_present, sample, used_llm }.
    """
    info = provider_info()
    text, used = _chat("You are a health-check probe.", "Reply with the single word: pong.", 0.0, 8)
    sample = (text or "").strip()
    if len(sample) > 64:
        sample = sample[:64] + "…"
    return {**info, "used_llm": used, "sample": sample}


# ------------------------------------------------------------------
# Helpers
# ------------------------------------------------------------------
def _safe(e: Exception) -> str:
    try:
        return str(e)
    except Exception:
        return e.__class__.__name__

