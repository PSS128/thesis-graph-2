# backend/app/routers/feedback.py
from __future__ import annotations

from typing import List, Optional, Literal
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlmodel import Session, select

from ..db import get_session
from ..models.store import Feedback, Project

router = APIRouter(prefix="/feedback", tags=["feedback"])

Target = Literal["essay", "outline"]

class FeedbackIn(BaseModel):
    project_id: int
    target: Target
    target_index: Optional[int] = None
    rating: int  # +1 or -1
    comment: Optional[str] = None

class FeedbackOut(BaseModel):
    id: int
    project_id: int
    target: Target
    target_index: Optional[int] = None
    rating: int
    comment: Optional[str] = None
    created_at: str

class FeedbackSummary(BaseModel):
    project_id: int
    essay_up: int
    essay_down: int
    outline_up: int
    outline_down: int

@router.post("", response_model=FeedbackOut)
def create_feedback(data: FeedbackIn, session: Session = Depends(get_session)):
    if data.rating not in (-1, 1):
        raise HTTPException(status_code=400, detail="rating must be +1 or -1")
    proj = session.get(Project, data.project_id)
    if not proj:
        raise HTTPException(status_code=404, detail="project not found")
    if data.target == "outline" and data.target_index is None:
        raise HTTPException(status_code=400, detail="outline feedback requires target_index")

    fb = Feedback(
        project_id=data.project_id,
        target=data.target,
        target_index=data.target_index,
        rating=data.rating,
        comment=(data.comment or None),
    )
    session.add(fb)
    session.commit()
    session.refresh(fb)
    return FeedbackOut(
        id=fb.id,
        project_id=fb.project_id,
        target=fb.target,  # type: ignore
        target_index=fb.target_index,
        rating=fb.rating,
        comment=fb.comment,
        created_at=fb.created_at.isoformat(),
    )

@router.get("", response_model=List[FeedbackOut])
def list_feedback(project_id: int, session: Session = Depends(get_session)):
    rows = session.exec(select(Feedback).where(Feedback.project_id == project_id).order_by(Feedback.id.desc())).all()
    return [
        FeedbackOut(
            id=r.id,
            project_id=r.project_id,
            target=r.target,  # type: ignore
            target_index=r.target_index,
            rating=r.rating,
            comment=r.comment,
            created_at=r.created_at.isoformat(),
        )
        for r in rows
    ]

@router.get("/summary/{project_id}", response_model=FeedbackSummary)
def summary(project_id: int, session: Session = Depends(get_session)):
    qs = session.exec(select(Feedback).where(Feedback.project_id == project_id)).all()
    essay_up = sum(1 for x in qs if x.target == "essay" and x.rating == 1)
    essay_down = sum(1 for x in qs if x.target == "essay" and x.rating == -1)
    outline_up = sum(1 for x in qs if x.target == "outline" and x.rating == 1)
    outline_down = sum(1 for x in qs if x.target == "outline" and x.rating == -1)
    return FeedbackSummary(
        project_id=project_id,
        essay_up=essay_up,
        essay_down=essay_down,
        outline_up=outline_up,
        outline_down=outline_down,
    )
