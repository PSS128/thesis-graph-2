# backend/app/routers/debug.py
from fastapi import APIRouter
from ..services import llm

router = APIRouter(prefix="/debug", tags=["debug"])

@router.get("/llm")
def debug_llm():
    """
    Returns an object describing whether the LLM is reachable.
    Example:
      {"ok": true, "provider": "groq", "model": "llama-3.3-70b-versatile", "sample": "pong"}
    """
    return llm.ping()
