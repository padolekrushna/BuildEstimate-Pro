from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from backend.database import get_db
from backend.models.dsr_item import DSRItem
from backend.schemas.dsr_item import DSRItemOut

router = APIRouter()


@router.get("/search", response_model=list[DSRItemOut])
def search_dsr(q: str = Query(..., min_length=1), db: Session = Depends(get_db)):
    qterm = f"%{q.lower()}%"
    items = db.query(DSRItem).filter(DSRItem.description.ilike(qterm)).limit(50).all()
    return items


@router.get("/items/{item_id}", response_model=DSRItemOut)
def get_item(item_id: int, db: Session = Depends(get_db)):
    item = db.query(DSRItem).filter(DSRItem.id == item_id).first()
    if not item:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="DSR item not found")
    return item
