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
from ..models.store import Project, GraphNode, GraphEdge, User
from ..dependencies.auth import get_current_user

logger = logging.getLogger("uvicorn.error")

router = APIRouter(prefix="/projects", tags=["projects"])

# ---------- Schemas ----------
NodeType = Literal["THESIS", "CLAIM", "EVIDENCE", "VARIABLE"]
RelationType = Literal["SUPPORTS", "CONTRADICTS", "DEFINES"]

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
def _verify_project_ownership(project: Project, user: User) -> None:
    """Verify that the user owns the project, raise 403 if not"""
    if project.user_id != user.id:
        raise HTTPException(
            status_code=403,
            detail="You don't have permission to access this project"
        )

def _node_to_dict(n: GraphNode) -> dict:
    """Convert GraphNode to dict, supporting both old and new schema"""
    import json

    return {
        "id": n.node_id,
        # Support both old (text/type) and new (name/kind) fields
        "text": n.text or n.name,  # Fallback to name if text is None
        "type": n.type or n.kind,  # Fallback to kind if type is None
        "name": n.name if hasattr(n, 'name') else n.text,
        "kind": n.kind if hasattr(n, 'kind') else n.type,
        "definition": n.definition if hasattr(n, 'definition') else None,
        "synonyms": json.loads(n.synonyms) if n.synonyms else [],
        "measurement_ideas": json.loads(n.measurement_ideas) if n.measurement_ideas else [],
        "citations": json.loads(n.citations) if n.citations else [],
        "x": n.x,
        "y": n.y,
    }

def _edge_to_dict(e: GraphEdge) -> dict:
    """Convert GraphEdge to dict, supporting both old and new schema"""
    import json

    return {
        "from_id": e.from_id,
        "to_id": e.to_id,
        # Support both old (relation) and new (type) fields
        "relation": e.relation or e.type,  # Fallback to type if relation is None
        "type": e.type if hasattr(e, 'type') else e.relation,
        "status": e.status if hasattr(e, 'status') else "ACCEPTED",
        "mechanisms": json.loads(e.mechanisms) if e.mechanisms else [],
        "assumptions": json.loads(e.assumptions) if e.assumptions else [],
        "confounders": json.loads(e.confounders) if e.confounders else [],
        "citations": json.loads(e.citations) if e.citations else [],
        "rationale": e.rationale,
        "confidence": e.confidence,
    }

# ---------- Routes ----------
@router.get("", response_model=List[ProjectMeta])
def list_projects(
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    """List all projects owned by the current user"""
    rows = session.exec(
        select(Project)
        .where(Project.user_id == current_user.id)
        .order_by(Project.id)
    ).all()
    return [{"id": p.id, "title": p.title} for p in rows]

@router.post("", response_model=ProjectMeta)
def create_project(
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
    title: Optional[str] = Query(default=None),
    data: Optional[CreateProjectIn] = None,
):
    """Create a new project owned by the current user"""
    final_title = title or (data.title if data else None) or "Untitled Project"
    proj = Project(title=final_title, user_id=current_user.id)
    session.add(proj)
    session.commit()
    session.refresh(proj)
    return {"id": proj.id, "title": proj.title}

@router.get("/{project_id}", response_model=LoadResponse)
def load_project(
    project_id: int,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    """Load a project (only if owned by current user)"""
    proj = session.get(Project, project_id)
    if not proj:
        raise HTTPException(status_code=404, detail="Project not found")

    _verify_project_ownership(proj, current_user)

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
    current_user: User = Depends(get_current_user)
):
    """Save project nodes and edges (only if owned by current user)"""
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

    _verify_project_ownership(proj, current_user)

    try:
        # wipe existing
        for n in session.exec(select(GraphNode).where(GraphNode.project_id == project_id)).all():
            session.delete(n)
        for e in session.exec(select(GraphEdge).where(GraphEdge.project_id == project_id)).all():
            session.delete(e)

        # insert nodes
        import json
        for n in nodes:
            nid = n.get("id")
            if not nid:
                continue

            # Support both old and new schema
            name = n.get("name") or n.get("text") or "Untitled Node"
            kind = n.get("kind") or n.get("type") or "VARIABLE"

            session.add(
                GraphNode(
                    project_id=project_id,
                    node_id=str(nid),
                    name=str(name),
                    kind=str(kind),
                    definition=n.get("definition"),
                    text=n.get("text"),  # Keep for backward compatibility
                    type=n.get("type"),  # Keep for backward compatibility
                    synonyms=json.dumps(n.get("synonyms", [])) if n.get("synonyms") else None,
                    measurement_ideas=json.dumps(n.get("measurement_ideas", [])) if n.get("measurement_ideas") else None,
                    citations=json.dumps(n.get("citations", [])) if n.get("citations") else None,
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

            # Support both old and new schema
            edge_type = e.get("type") or e.get("relation") or "CAUSES"
            edge_status = e.get("status") or "PROPOSED"

            session.add(
                GraphEdge(
                    project_id=project_id,
                    from_id=str(f),
                    to_id=str(t),
                    type=str(edge_type),
                    status=str(edge_status),
                    relation=e.get("relation"),  # Keep for backward compatibility
                    mechanisms=json.dumps(e.get("mechanisms", [])) if e.get("mechanisms") else None,
                    assumptions=json.dumps(e.get("assumptions", [])) if e.get("assumptions") else None,
                    confounders=json.dumps(e.get("confounders", [])) if e.get("confounders") else None,
                    citations=json.dumps(e.get("citations", [])) if e.get("citations") else None,
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
def rename_project(
    project_id: int,
    data: RenameProjectIn,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    """Rename a project (only if owned by current user)"""
    proj = session.get(Project, project_id)
    if not proj:
        raise HTTPException(status_code=404, detail="Project not found")

    _verify_project_ownership(proj, current_user)

    proj.title = data.title or proj.title
    session.add(proj)
    session.commit()
    session.refresh(proj)
    return {"id": proj.id, "title": proj.title}

# ---- Delete (cascade via Python-level deletes) ----
@router.delete("/{project_id}")
def delete_project(
    project_id: int,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    """Delete a project (only if owned by current user)"""
    proj = session.get(Project, project_id)
    if not proj:
        raise HTTPException(status_code=404, detail="Project not found")

    _verify_project_ownership(proj, current_user)

    # delete children first
    for n in session.exec(select(GraphNode).where(GraphNode.project_id == project_id)).all():
        session.delete(n)
    for e in session.exec(select(GraphEdge).where(GraphEdge.project_id == project_id)).all():
        session.delete(e)
    session.delete(proj)
    session.commit()
    return {"ok": True, "deleted": project_id}

@router.get("/{project_id}/export", response_model=ExportPayload)
def export_project(
    project_id: int,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    """Export a project as JSON (only if owned by current user)"""
    proj = session.get(Project, project_id)
    if not proj:
        raise HTTPException(status_code=404, detail="Project not found")

    _verify_project_ownership(proj, current_user)

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
def import_project(
    payload: ImportPayload,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    """Import a project from JSON (creates new project owned by current user)"""
    title = (payload.project.title if payload.project else None) or "Imported Project"
    proj = Project(title=title, user_id=current_user.id)
    session.add(proj)
    session.commit()
    session.refresh(proj)

    import json
    for n in payload.nodes:
        session.add(
            GraphNode(
                project_id=proj.id,
                node_id=n.id,
                name=getattr(n, 'name', n.text),
                kind=getattr(n, 'kind', n.type),
                definition=getattr(n, 'definition', None),
                text=n.text,  # Keep for backward compatibility
                type=n.type,  # Keep for backward compatibility
                synonyms=json.dumps(getattr(n, 'synonyms', [])) if hasattr(n, 'synonyms') and n.synonyms else None,
                measurement_ideas=json.dumps(getattr(n, 'measurement_ideas', [])) if hasattr(n, 'measurement_ideas') and n.measurement_ideas else None,
                citations=json.dumps(getattr(n, 'citations', [])) if hasattr(n, 'citations') and n.citations else None,
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
                type=getattr(e, 'type', e.relation),
                status=getattr(e, 'status', 'ACCEPTED'),
                relation=e.relation,  # Keep for backward compatibility
                mechanisms=json.dumps(getattr(e, 'mechanisms', [])) if hasattr(e, 'mechanisms') and e.mechanisms else None,
                assumptions=json.dumps(getattr(e, 'assumptions', [])) if hasattr(e, 'assumptions') and e.assumptions else None,
                confounders=json.dumps(getattr(e, 'confounders', [])) if hasattr(e, 'confounders') and e.confounders else None,
                citations=json.dumps(getattr(e, 'citations', [])) if hasattr(e, 'citations') and e.citations else None,
                rationale=e.rationale,
                confidence=e.confidence,
            )
        )

    session.commit()
    return {"id": proj.id, "title": proj.title}
