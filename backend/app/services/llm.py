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
import time
from typing import Any, Dict, List, Optional, Tuple
from . import cache
from ..prompts.version import PromptVersions, make_cache_key_with_version, get_version_header
load_dotenv()

# --- API keys ---
GROQ_API_KEY = os.getenv("GROQ_API_KEY")


# ------------------------------------------------------------------
# Metrics logging
# ------------------------------------------------------------------
def _log_llm_metrics(
    prompt_type: str,
    latency_ms: int,
    success: bool,
    cache_hit: bool = False,
    error_message: Optional[str] = None,
    input_tokens: Optional[int] = None,
    output_tokens: Optional[int] = None,
):
    """
    Log LLM API call metrics to database for monitoring and optimization.
    This runs in a try-except to never block the main LLM flow.
    """
    try:
        from ..models.store import LLMMetrics
        from ..db import get_session

        version = PromptVersions.get_version(prompt_type)

        metric = LLMMetrics(
            prompt_type=prompt_type,
            prompt_version=version,
            latency_ms=latency_ms,
            success=success,
            cache_hit=cache_hit,
            error_message=error_message,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
        )

        # Get a database session and save
        with next(get_session()) as session:
            session.add(metric)
            session.commit()

    except Exception as e:
        # Never crash the app due to metrics logging
        print(f"[METRICS LOG ERROR] {e}")


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
    except json.JSONDecodeError as e:
        # Try one more time with strict escaping of control characters
        print(f"[JSON PARSE ERROR] {_safe(e)} - Attempting control character fix")
        try:
            # Use json.loads with strict=False to be more lenient
            import ast
            # Try to fix by replacing unescaped newlines within string values
            fixed_chunk = re.sub(r'("(?:[^"\\]|\\.)*")', lambda m: m.group(1).replace('\n', '\\n').replace('\r', '\\r').replace('\t', '\\t'), chunk)
            return json.loads(fixed_chunk, strict=False)
        except Exception as e2:
            print(f"[JSON PARSE ERROR FINAL] {_safe(e2)}\nTEXT: {text[:400]}")
            return None
    except Exception as e:
        print(f"[JSON PARSE ERROR] {_safe(e)}\nTEXT: {text[:400]}")
        return None


def chat_json(
    system_prompt: str,
    user_prompt: str,
    temperature: float = 0.2,
    max_tokens: int = 1200,
    prompt_type: str = "generic",  # For versioning: "node_extraction", "edge_rationale", etc.
) -> Optional[Dict[str, Any]]:
    """
    Ask for strict JSON and parse it. Returns dict or None.
    Uses OpenAI JSON mode when available to reduce parse failures.
    Caches responses for faster repeated queries.

    prompt_type: Used for versioning in cache keys (optional, defaults to "generic")
    """
    start_time = time.time()

    # Check cache first (with version in key)
    cache_key_args = make_cache_key_with_version(prompt_type, system_prompt, user_prompt, temperature, max_tokens)
    cached = cache.get(*cache_key_args, ttl=cache.LLM_CACHE_TTL)
    if cached is not None:
        latency_ms = int((time.time() - start_time) * 1000)
        # Log cache hit
        _log_llm_metrics(prompt_type, latency_ms, success=True, cache_hit=True)
        return cached

    # Strengthen the instruction regardless of provider.
    sys = (system_prompt or "") + "\n\nCRITICAL JSON FORMATTING:\n- Return ONLY a single valid JSON object\n- Start with '{' and end with '}'\n- NO newlines inside string values - use \\n for line breaks\n- Use escaped quotes for quotes inside strings: \\\"  \n- Ensure all JSON is on a single line or properly escaped"
    usr = user_prompt

    text, used = _chat(sys, usr, temperature=temperature, max_tokens=max_tokens, json_mode=True)
    latency_ms = int((time.time() - start_time) * 1000)

    data = _extract_json_strict(text)
    if data is not None:
        # Cache successful result
        cache.set(data, *cache_key_args)
        # Log successful LLM call
        _log_llm_metrics(prompt_type, latency_ms, success=True, cache_hit=False)
        return data

    # Second chance with relaxed fixups (helps Groq or non-JSON-mode outputs)
    data = _extract_json_relaxed(text)
    if data is not None:
        # Cache successful result
        cache.set(data, *cache_key_args)
        # Log successful LLM call (with parsing workaround)
        _log_llm_metrics(prompt_type, latency_ms, success=True, cache_hit=False)
        return data

    # Failed to parse JSON
    print("[chat_json] model did not return strict JSON; using None fallback.")
    _log_llm_metrics(prompt_type, latency_ms, success=False, cache_hit=False,
                     error_message="Failed to parse JSON response")
    return None


# ------------------------------------------------------------------
# Compose helper
# ------------------------------------------------------------------
def _validate_citation_format(essay_text: str) -> Tuple[bool, List[str]]:
    """
    Validate citation format in essay_with_citations.
    Returns (is_valid, warnings_list).

    Expected format: [Evidence: "quote text"]
    Invalid formats: [1], (Author 2024), [Evidence 1], etc.
    """
    if not essay_text:
        return True, []

    warnings = []

    # Check for correct format [Evidence: "..."]
    correct_pattern = r'\[Evidence:\s*"[^"]+"\]'
    correct_citations = re.findall(correct_pattern, essay_text)

    # Check for common wrong formats
    wrong_patterns = [
        (r'\[\d+\]', 'numbered citations like [1]'),
        (r'\([A-Z][a-z]+\s+\d{4}\)', 'author-year citations like (Smith 2024)'),
        (r'\[Evidence\s+\d+\]', 'numbered evidence like [Evidence 1]'),
        (r'\[Evidence:\s*[^"]+\](?!\s*")', 'evidence without quotes'),
    ]

    for pattern, description in wrong_patterns:
        matches = re.findall(pattern, essay_text)
        if matches:
            warnings.append(f"Found {len(matches)} {description}: {matches[:3]}")

    # Check if there are citations but none in correct format
    has_brackets = '[' in essay_text and ']' in essay_text
    if has_brackets and not correct_citations and not warnings:
        warnings.append("Citations found but format unclear - expected [Evidence: \"quote\"]")

    is_valid = len(warnings) == 0 or len(correct_citations) > 0
    return is_valid, warnings


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
    start_time = time.time()

    # Create cache key from inputs (with version)
    node_lines = "\n".join(f"- {n.get('text','').strip()}" for n in nodes if n.get("text"))
    cache_key_args = make_cache_key_with_version("composition", thesis, node_lines, words, audience, tone)

    # Check cache first (6 hour TTL for composition as it's semi-dynamic)
    cached = cache.get(*cache_key_args, ttl=21600)  # 6 hours = 21600 seconds
    if cached is not None:
        latency_ms = int((time.time() - start_time) * 1000)
        _log_llm_metrics("composition", latency_ms, success=True, cache_hit=True)
        return cached, True  # Return cached result with used=True

    # Separate nodes by type for better organization
    claims = [n for n in nodes if n.get("type") == "CLAIM"]
    evidence = [n for n in nodes if n.get("type") == "EVIDENCE"]
    variables = [n for n in nodes if n.get("type") == "VARIABLE"]

    # Build claim-evidence mapping from edges
    claim_evidence_map = {}
    for edge in edges:
        if edge.get("relation") == "SUPPORTS":
            from_id = edge.get("from_id")
            to_id = edge.get("to_id")
            # Find evidence and claim nodes
            from_node = next((n for n in nodes if n.get("id") == from_id), None)
            to_node = next((n for n in nodes if n.get("id") == to_id), None)

            if from_node and to_node and from_node.get("type") == "EVIDENCE" and to_node.get("type") == "CLAIM":
                if to_id not in claim_evidence_map:
                    claim_evidence_map[to_id] = []
                claim_evidence_map[to_id].append(from_node.get("text", ""))

    # Build formatted strings
    claims_text = "\n".join(f"- {c.get('text','').strip()}" for c in claims if c.get("text"))
    evidence_text = "\n".join(f"- {e.get('text','').strip()}" for e in evidence if e.get("text"))
    variables_text = "\n".join(f"- {v.get('text','').strip()}" for v in variables if v.get("text"))

    # Build claim-evidence connections text
    connections_text = ""
    for claim_id, evidences in claim_evidence_map.items():
        claim = next((c for c in claims if c.get("id") == claim_id), None)
        if claim:
            connections_text += f"\nClaim: {claim.get('text', '')}\n"
            connections_text += "Evidence:\n"
            for ev in evidences:
                connections_text += f"  - {ev}\n"

    system_prompt = (
        "You are an expert academic writer that produces clear, concise, evidence-based essays. "
        "Return STRICT JSON ONLY with three fields: outline, essay_md, essay_with_citations. "
        "No extra text, no markdown code fences, just pure JSON."
    )
    user_prompt = (
        f"Thesis: {thesis or ''}\n\n"
        f"Claims:\n{claims_text}\n\n"
        f"Evidence:\n{evidence_text}\n\n"
        f"Variables:\n{variables_text}\n\n"
        f"Claim-Evidence Connections:\n{connections_text}\n\n"
        f"Audience: {audience} | Tone: {tone} | Target Words: {words}\n\n"
        "TASK: Write an outline and TWO essay versions.\n\n"
        "CRITICAL REQUIREMENTS:\n"
        "1. NO REPETITION: Each piece of evidence and each claim should appear ONLY ONCE in the essay\n"
        "2. UNIQUE CONTENT: If a claim or evidence is mentioned, do not restate it in different words\n"
        "3. MARKDOWN STRUCTURE:\n"
        "   - Use ## for ALL section headings (Introduction, Body sections, Conclusion, Limitations & Counterarguments)\n"
        "   - Use blank lines between ALL paragraphs\n"
        "   - Each paragraph: 3-5 sentences\n"
        "4. CONTENT FLOW:\n"
        "   - Introduction: Present thesis clearly without evidence\n"
        "   - Body: Group related claims by theme, each with supporting evidence\n"
        "   - Limitations & Counterarguments: Acknowledge alternative explanations, confounding variables, gaps in evidence\n"
        "   - Conclusion: Synthesize main points WITHOUT repeating evidence\n"
        "5. TRANSITIONS: Use smooth transitions between paragraphs and sections\n\n"
        "TWO SEPARATE ESSAY FIELDS (IMPORTANT - WRITE EACH ESSAY ONLY ONCE):\n\n"
        "Field 'essay_md' - Clean version:\n"
        "   - Write the complete essay WITHOUT any citations\n"
        "   - Just flowing narrative text\n"
        "   - Use **bold** for key points and *italics* for claims\n"
        "   - Write this essay ONCE in the essay_md field\n\n"
        "Field 'essay_with_citations' - Version with evidence:\n"
        "   - Start fresh - write the SAME essay again\n"
        "   - This time ADD citations in this EXACT format: [Evidence: \"direct quote\"]\n"
        "   - CRITICAL CITATION FORMAT RULES:\n"
        "     ✓ CORRECT: [Evidence: \"GDP growth accelerated in Q3\"]\n"
        "     ✓ CORRECT: [Evidence: \"4-day workweek reduced burnout by 23%\"]\n"
        "     ✗ WRONG: [1] or (Smith 2024) or [Evidence 1] or any other format\n"
        "   - Keep citations brief (max 15 words of quoted text)\n"
        "   - Place citations immediately after the sentence they support\n"
        "   - Write this essay ONCE in the essay_with_citations field\n\n"
        "CRITICAL: Each field should contain ONE complete essay, not repeated content!\n\n"
        "CITATION FORMAT EXAMPLES:\n"
        "- Studies show burnout decreased significantly [Evidence: \"employees reported 40% less emotional exhaustion\"].\n"
        "- Economic growth accelerated [Evidence: \"GDP rose 3.2% in the fourth quarter\"] during this period.\n"
        "- Performance improved across metrics [Evidence: \"productivity increased while maintaining output quality\"].\n\n"
        "OUTPUT FORMAT:\n"
        '{{"outline":[...], "essay_md":"<WRITE CLEAN ESSAY HERE>", "essay_with_citations":"<WRITE CITED ESSAY HERE>"}}\n\n'
        "DO NOT write the essay twice in the same field!"
    )

    text, used = _chat(system_prompt, user_prompt, temperature=0.5, max_tokens=2500, json_mode=True)
    latency_ms = int((time.time() - start_time) * 1000)

    # Prefer strict JSON
    data = _extract_json_strict(text) or _extract_json_relaxed(text) or {}
    if data.get("outline") and data.get("essay_md"):
        # Ensure essay_with_citations exists (backwards compatibility)
        if "essay_with_citations" not in data:
            data["essay_with_citations"] = data.get("essay_md", "")

        # Validate citation format
        essay_with_citations = data.get("essay_with_citations", "")
        is_valid, warnings = _validate_citation_format(essay_with_citations)
        if warnings:
            print(f"[CITATION FORMAT WARNING] {'; '.join(warnings)}")
            # Add warnings to metadata (optional - could be exposed to frontend)
            data["_citation_warnings"] = warnings

        # Cache successful result
        cache.set(data, *cache_key_args)
        # Log successful composition
        _log_llm_metrics("composition", latency_ms, success=True, cache_hit=False)
        return data, used

    # Salvage the model text if we got any — keep used=True so the badge flips on.
    if used and isinstance(text, str) and text.strip():
        heading = thesis or "Argument Overview"
        pts = [n.get("text", "") for n in nodes][:5]
        outline = [{"heading": heading, "points": [p for p in pts if p]}]
        # Log partial success (salvaged result)
        _log_llm_metrics("composition", latency_ms, success=True, cache_hit=False,
                        error_message="Salvaged result - JSON parsing failed")
        return {"outline": outline, "essay_md": text, "essay_with_citations": text}, True

    # True deterministic fallback (no model used)
    heading = thesis or "Argument Overview"
    pts = [n.get("text", "") for n in nodes][:5]
    outline = [{"heading": heading, "points": [p for p in pts if p]}]
    essay_md = f"## {heading}\n\n" + "\n\n".join(f"- {p}" for p in pts if p)
    # Log fallback (LLM unavailable)
    _log_llm_metrics("composition", latency_ms, success=False, cache_hit=False,
                    error_message="LLM unavailable or failed")
    return {"outline": outline, "essay_md": essay_md, "essay_with_citations": ""}, False


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

