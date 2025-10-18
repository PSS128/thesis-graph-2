from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from ..services.embeddings import add_document
import pdfplumber
import io

router = APIRouter(prefix="/ingest", tags=["ingest"])

@router.post("/upload")
async def upload(file: UploadFile = File(...), title: str = Form(None)):
    name = file.filename or "uploaded"
    title = title or name
    content_type = (file.content_type or "").lower()

    # Extract text
    data = await file.read()
    text = ""
    try:
        if name.lower().endswith(".pdf") or "pdf" in content_type:
            # Wrap bytes in BytesIO to provide seek() method
            pdf_file = io.BytesIO(data)
            with pdfplumber.open(pdf_file) as pdf:
                parts = [page.extract_text() or "" for page in pdf.pages]
                text = "\n".join(parts)
        else:
            text = data.decode("utf-8", errors="ignore")
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to read file: {e}")

    if not text.strip():
        raise HTTPException(status_code=400, detail="No text extracted from file.")

    res = add_document(doc_title=title, source=name, text=text)
    return {"ok": True, "doc_id": res.get("doc_id"), **res}
