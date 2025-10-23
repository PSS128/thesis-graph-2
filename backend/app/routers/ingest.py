from fastapi import APIRouter, UploadFile, File, Form, HTTPException, BackgroundTasks
from pathlib import Path
from ..services.embeddings import add_document
import pdfplumber
import hashlib

router = APIRouter(prefix="/ingest", tags=["ingest"])

# Storage configuration
STORAGE = Path(__file__).resolve().parent.parent / "storage"
UPLOAD_DIR = STORAGE / "uploads"
UPLOAD_DIR.mkdir(exist_ok=True)

def _hash(s: str) -> str:
    return hashlib.sha1(s.encode("utf-8")).hexdigest()[:12]

def process_pdf_background(doc_id: str, doc_title: str, filename: str, file_path: Path):
    """Extract text from PDF and generate embeddings in background thread"""
    try:
        print(f"[Background] Starting processing for: {doc_title}")

        # Extract text from saved PDF
        text = ""
        if filename.lower().endswith(".pdf"):
            with pdfplumber.open(file_path) as pdf:
                parts = [page.extract_text() or "" for page in pdf.pages]
                text = "\n".join(parts)
        else:
            # Handle plain text files
            text = file_path.read_text(encoding="utf-8", errors="ignore")

        # Generate embeddings
        add_document(doc_title=doc_title, source=filename, text=text)

        # Clean up file after successful processing
        file_path.unlink(missing_ok=True)

        print(f"[Background] Completed processing for: {doc_title}")
    except Exception as e:
        print(f"[Background] Failed to process {doc_title}: {e}")
        # Clean up file even on error
        if file_path.exists():
            file_path.unlink(missing_ok=True)

@router.post("/upload")
async def upload(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    title: str = Form(None)
):
    name = file.filename or "uploaded"
    title = title or name

    # Read file bytes (fast - <1 second even for large PDFs)
    data = await file.read()

    if not data:
        raise HTTPException(status_code=400, detail="Empty file uploaded.")

    # Generate doc_id immediately
    doc_id = _hash(title + name)

    # Save file to disk (fast - <1 second)
    file_extension = Path(name).suffix or ".pdf"
    file_path = UPLOAD_DIR / f"{doc_id}{file_extension}"

    try:
        file_path.write_bytes(data)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to save file: {e}")

    # Schedule PDF extraction + embedding generation in background
    background_tasks.add_task(process_pdf_background, doc_id, title, name, file_path)

    # Return IMMEDIATELY (user gets instant feedback!)
    return {
        "ok": True,
        "doc_id": doc_id,
        "status": "processing",
        "message": "Upload complete. Processing document in background..."
    }
