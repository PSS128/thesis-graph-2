# backend/app/routers/projects.py
from __future__ import annotations

"""
Project routes for Thesis Graph.

Endpoints
---------
GET    /projects                     -> list projects
POST   /projects                     -> create project (?title= or body {"title": ...})
GET    /projects/{project_id}        -> load project (project, nodes, edges)
POST   /projects/{project_id}/save   -> save nodes/edges (permissive body; logs errors)
PATCH  /projects/{project_id}        -> rename project {"title": "..."}
DELETE /projects/{project_id}        -> delete project (cascades nodes/edges)
GET    /projects/{project_id}/export -> export JSON
POST   /projects/import              -> import JSON -> returns new project meta
"""

from typing import List, Optional, Literal
import logging

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from pydantic import BaseModel
from sqlmodel import Session, select

from ..db import get_session
from ..models.store import Project, GraphNode, GraphEdge

logger = logging.getLogger("uvicorn.error")

router = APIRouter(prefix="/projects", tags=["projects"])

# ---------- Schemas ----------
NodeType = Literal["THESIS", "CLAIM"]
RelationType = Literal["SUPPORTS", "CONTRADICTS"]

class ProjectMeta(BaseModel):
    id: int
    title: str

class NodeIn(BaseModel):
    id: str
    text: str
    type: NodeType
    x: Optional[float] = None
    y: Optional[float] = None

class EdgeIn(BaseModel):
    from_id: str
    to_id: str
    relation: RelationType
    rationale: Optional[str] = None
    confidence: Optional[float] = None

class SavePayload(BaseModel):
    nodes: List[NodeIn] = []
    edges: List[EdgeIn] = []

class LoadResponse(BaseModel):
    project: ProjectMeta
    nodes: List[NodeIn]
    edges: List[EdgeIn]

class ExportPayload(BaseModel):
    project: ProjectMeta
    nodes: List[NodeIn]
    edges: List[EdgeIn]

class ImportPayload(BaseModel):
    project: Optional[ProjectMeta] = None
    nodes: List[NodeIn]
    edges: List[EdgeIn] = []

class CreateProjectIn(BaseModel):
    title: Optional[str] = None

class RenameProjectIn(BaseModel):
    title: str

# ---------- Helpers ----------
def _node_to_dict(n: GraphNode) -> dict:
    return {"id": n.node_id, "text": n.text, "type": n.type, "x": n.x, "y": n.y}

def _edge_to_dict(e: GraphEdge) -> dict:
    return {
        "from_id": e.from_id,
        "to_id": e.to_id,
        "relation": e.relation,
        "rationale": e.rationale,
        "confidence": e.confidence,
    }

# ---------- Routes ----------
@router.get("", response_model=List[ProjectMeta])
def list_projects(session: Session = Depends(get_session)):
    rows = session.exec(select(Project).order_by(Project.id)).all()
    return [{"id": p.id, "title": p.title} for p in rows]

@router.post("", response_model=ProjectMeta)
def create_project(
    session: Session = Depends(get_session),
    title: Optional[str] = Query(default=None),
    data: Optional[CreateProjectIn] = None,
):
    final_title = title or (data.title if data else None) or "Untitled Project"
    proj = Project(title=final_title)
    session.add(proj)
    session.commit()
    session.refresh(proj)
    return {"id": proj.id, "title": proj.title}

@router.get("/{project_id}", response_model=LoadResponse)
def load_project(project_id: int, session: Session = Depends(get_session)):
    proj = session.get(Project, project_id)
    if not proj:
        raise HTTPException(status_code=404, detail="Project not found")

    nodes = session.exec(
        select(GraphNode).where(GraphNode.project_id == project_id)
    ).all()
    edges = session.exec(
        select(GraphEdge).where(GraphEdge.project_id == project_id)
    ).all()

    return {
        "project": {"id": proj.id, "title": proj.title},
        "nodes": [_node_to_dict(n) for n in nodes],
        "edges": [_edge_to_dict(e) for e in edges],
    }

# ---- Permissive & logged save (prevents "Failed to fetch") ----
@router.post("/{project_id}/save")
async def save_project(
    project_id: int,
    request: Request,
    session: Session = Depends(get_session),
):
    try:
        body = await request.json()
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid JSON body")

    nodes = body.get("nodes", []) or []
    edges = body.get("edges", []) or []

    logger.info(f"[save] project={project_id} nodes={len(nodes)} edges={len(edges)}")

    proj = session.get(Project, project_id)
    if not proj:
        raise HTTPException(status_code=404, detail="Project not found")

    try:
        # wipe existing
        for n in session.exec(select(GraphNode).where(GraphNode.project_id == project_id)).all():
            session.delete(n)
        for e in session.exec(select(GraphEdge).where(GraphEdge.project_id == project_id)).all():
            session.delete(e)

        # insert nodes
        for n in nodes:
            nid = n.get("id")
            if not nid:
                continue
            session.add(
                GraphNode(
                    project_id=project_id,
                    node_id=str(nid),
                    text=str(n.get("text", "")),
                    type=str(n.get("type", "CLAIM")),
                    x=(n.get("x") if isinstance(n.get("x"), (int, float)) else None),
                    y=(n.get("y") if isinstance(n.get("y"), (int, float)) else None),
                )
            )

        # insert edges
        for e in edges:
            f = e.get("from_id")
            t = e.get("to_id")
            if not f or not t:
                continue
            session.add(
                GraphEdge(
                    project_id=project_id,
                    from_id=str(f),
                    to_id=str(t),
                    relation=str(e.get("relation", "SUPPORTS")),
                    rationale=e.get("rationale"),
                    confidence=e.get("confidence"),
                )
            )

        session.commit()
        logger.info(f"[save] OK project={project_id}")
        return {"ok": True, "project_id": project_id, "nodes": len(nodes), "edges": len(edges)}
    except Exception as ex:
        logger.exception(f"[save] failed project={project_id}")
        raise HTTPException(status_code=500, detail=str(ex))

# ---- Rename ----
@router.patch("/{project_id}", response_model=ProjectMeta)
def rename_project(project_id: int, data: RenameProjectIn, session: Session = Depends(get_session)):
    proj = session.get(Project, project_id)
    if not proj:
        raise HTTPException(status_code=404, detail="Project not found")
    proj.title = data.title or proj.title
    session.add(proj)
    session.commit()
    session.refresh(proj)
    return {"id": proj.id, "title": proj.title}

# ---- Delete (cascade via Python-level deletes) ----
@router.delete("/{project_id}")
def delete_project(project_id: int, session: Session = Depends(get_session)):
    proj = session.get(Project, project_id)
    if not proj:
        raise HTTPException(status_code=404, detail="Project not found")
    # delete children first
    for n in session.exec(select(GraphNode).where(GraphNode.project_id == project_id)).all():
        session.delete(n)
    for e in session.exec(select(GraphEdge).where(GraphEdge.project_id == project_id)).all():
        session.delete(e)
    session.delete(proj)
    session.commit()
    return {"ok": True, "deleted": project_id}

@router.get("/{project_id}/export", response_model=ExportPayload)
def export_project(project_id: int, session: Session = Depends(get_session)):
    proj = session.get(Project, project_id)
    if not proj:
        raise HTTPException(status_code=404, detail="Project not found")

    nodes = session.exec(
        select(GraphNode).where(GraphNode.project_id == project_id)
    ).all()
    edges = session.exec(
        select(GraphEdge).where(GraphEdge.project_id == project_id)
    ).all()

    return {
        "project": {"id": proj.id, "title": proj.title},
        "nodes": [_node_to_dict(n) for n in nodes],
        "edges": [_edge_to_dict(e) for e in edges],
    }

@router.post("/import", response_model=ProjectMeta)
def import_project(payload: ImportPayload, session: Session = Depends(get_session)):
    title = (payload.project.title if payload.project else None) or "Imported Project"
    proj = Project(title=title)
    session.add(proj)
    session.commit()
    session.refresh(proj)

    for n in payload.nodes:
        session.add(
            GraphNode(
                project_id=proj.id,
                node_id=n.id,
                text=n.text,
                type=n.type,
                x=n.x,
                y=n.y,
            )
        )
    for e in payload.edges:
        session.add(
            GraphEdge(
                project_id=proj.id,
                from_id=e.from_id,
                to_id=e.to_id,
                relation=e.relation,
                rationale=e.rationale,
                confidence=e.confidence,
            )
        )

    session.commit()
    return {"id": proj.id, "title": proj.title}
