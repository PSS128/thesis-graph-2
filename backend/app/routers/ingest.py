from fastapi import APIRouter, UploadFile, File, Form, HTTPException, BackgroundTasks
from ..services.embeddings import add_document
import pdfplumber
import io
import hashlib

router = APIRouter(prefix="/ingest", tags=["ingest"])

def _hash(s: str) -> str:
    return hashlib.sha1(s.encode("utf-8")).hexdigest()[:12]

def process_embeddings_background(doc_title: str, source: str, text: str):
    """Process embeddings in background thread"""
    try:
        print(f"[Background] Starting embedding generation for: {doc_title}")
        add_document(doc_title=doc_title, source=source, text=text)
        print(f"[Background] Completed embedding generation for: {doc_title}")
    except Exception as e:
        print(f"[Background] Failed to generate embeddings: {e}")

@router.post("/upload")
async def upload(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    title: str = Form(None)
):
    name = file.filename or "uploaded"
    title = title or name
    content_type = (file.content_type or "").lower()

    # Extract text (fast operation)
    data = await file.read()
    text = ""
    page_count = None

    try:
        if name.lower().endswith(".pdf") or "pdf" in content_type:
            # Wrap bytes in BytesIO to provide seek() method
            pdf_file = io.BytesIO(data)
            with pdfplumber.open(pdf_file) as pdf:
                page_count = len(pdf.pages)
                parts = [page.extract_text() or "" for page in pdf.pages]
                text = "\n".join(parts)
        else:
            text = data.decode("utf-8", errors="ignore")
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to read file: {e}")

    if not text.strip():
        raise HTTPException(status_code=400, detail="No text extracted from file.")

    # Generate doc_id immediately (same logic as add_document)
    doc_id = _hash(title + name)

    # Schedule embedding generation in background
    background_tasks.add_task(process_embeddings_background, title, name, text)

    # Return immediately with doc_id
    return {
        "ok": True,
        "doc_id": doc_id,
        "page_count": page_count,
        "status": "processing",
        "message": "Document uploaded. Embeddings are being generated in the background."
    }
