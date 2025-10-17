from fastapi import APIRouter
from pydantic import BaseModel
from typing import List
from ..services.embeddings import retrieve

router = APIRouter(prefix="/retrieve", tags=["retrieve"])

class RetrieveReq(BaseModel):
    query: str
    top_k: int = 3

@router.post("", response_model=List[dict])
def do_retrieve(req: RetrieveReq):
    return retrieve(req.query, k=req.top_k)
