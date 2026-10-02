from fastapi import APIRouter, UploadFile, File, HTTPException, Query, Depends
from pathlib import Path
from sqlalchemy.orm import Session
from backend.database import get_db
from backend.services.dsr_service import ingest_and_index, semantic_search
from backend.services.gemini_service import GeminiService
from backend.services.ssr_ingestion_service import import_ssr_pdf_to_db
from backend.models.dsr_item import DSRItem

router = APIRouter()
DEFAULT_PDF = Path(__file__).parents[2] / "knowledge_base" / "PWD Civil SSR_2022-23_Final.pdf"


@router.post("/ingest")
async def ingest_dsr(file: UploadFile = File(...)):
    uploads = Path(__file__).parents[3] / "data" / "uploads"
    uploads.mkdir(parents=True, exist_ok=True)
    safe_name = Path(file.filename or "upload.pdf").name
    if Path(safe_name).suffix.lower() != ".pdf":
        raise HTTPException(status_code=415, detail="Only PDF uploads are supported")
    dest = uploads / safe_name
    try:
        with open(dest, 'wb') as f:
            content = await file.read(50 * 1024 * 1024 + 1)
            if len(content) > 50 * 1024 * 1024:
                raise HTTPException(status_code=413, detail="PDF exceeds the 50 MB upload limit")
            f.write(content)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    try:
        result = ingest_and_index(str(dest))
        return {"status": "ok", "result": result}
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Uploaded file not found after save")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/semantic_search")
def dsr_semantic_search(q: str = Query(..., min_length=1), top_k: int = Query(5, ge=1, le=25)):
    try:
        hits = semantic_search(q, top_k=top_k)
        return {"query": q, "results": hits}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/pdf_search")
def dsr_pdf_search(q: str = Query(..., min_length=1), pdf_path: str | None = None):
    try:
        pdf = Path(pdf_path) if pdf_path else DEFAULT_PDF
        allowed_roots = [DEFAULT_PDF.parent.resolve(), (Path(__file__).parents[3] / "data" / "uploads").resolve()]
        resolved_pdf = pdf.resolve()
        if not any(root == resolved_pdf.parent or root in resolved_pdf.parents for root in allowed_roots):
            raise HTTPException(status_code=400, detail="PDF path is outside the allowed knowledge or upload directories")
        if not pdf.exists():
            raise FileNotFoundError(str(pdf))
        service = GeminiService()
        answer = service.ask(q, str(pdf))
        return {"query": q, "pdf": str(pdf), "answer": answer}
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@router.post("/import-ssr")
def import_ssr(db: Session = Depends(get_db), pdf_path: str | None = None, limit: int = Query(100, ge=1, le=5000)):
    try:
        if pdf_path:
            candidate = Path(pdf_path).resolve()
            allowed_root = DEFAULT_PDF.parent.resolve()
            if allowed_root not in candidate.parents and candidate != DEFAULT_PDF.resolve():
                raise HTTPException(status_code=400, detail="PDF path is outside the knowledge-base directory")
        result = import_ssr_pdf_to_db(db, pdf_path=pdf_path, limit=limit)
        return {"status": "ok", "result": result}
    except Exception as exc:
        if isinstance(exc, HTTPException):
            raise
        raise HTTPException(status_code=500, detail=str(exc))


@router.get("/items")
def list_dsr_items(db: Session = Depends(get_db), q: str | None = None, limit: int = Query(50, ge=1, le=5000)):
    query = db.query(DSRItem)
    if q:
        query = query.filter(DSRItem.description.ilike(f"%{q}%") | DSRItem.item_no.ilike(f"%{q}%"))
    return query.order_by(DSRItem.id.asc()).limit(limit).all()
