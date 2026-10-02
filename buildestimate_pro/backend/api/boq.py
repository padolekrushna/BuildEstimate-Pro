from fastapi import APIRouter, Depends, Response, HTTPException
from sqlalchemy.orm import Session
from backend.database import get_db
from backend.services.boq_engine import generate_boq_for_project
from backend.services.excel_export import boq_to_excel_bytes

router = APIRouter()


@router.get("/{project_id}/boq")
def get_boq_items(project_id: int, db: Session = Depends(get_db)):
    """Return the calculated BOQ rows for the guided estimate pipeline."""
    from backend.models.project import Project
    if not db.query(Project).filter(Project.id == project_id).first():
        raise HTTPException(status_code=404, detail="Project not found")
    result = generate_boq_for_project(db, project_id)
    return result.get("boq", [])


@router.get("/{project_id}/summary")
def get_boq_summary(project_id: int, db: Session = Depends(get_db)):
    """Fetch BOQ summary with totals for a project."""
    from backend.models.project import Project
    result = generate_boq_for_project(db, project_id)
    boq = result.get("boq", [])
    materials = result.get("materials", [])
    labour = result.get("labour", [])
    
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    total_amount = sum([item.get("amount") or 0.0 for item in boq])
    item_count = len(boq)
    unpriced_items = sum(1 for item in boq if item.get("amount") is None or not item.get("dsr_unit_matches", True))
    
    return {
        "project_id": project_id,
        "project_name": project.name if project else f"Project {project_id}",
        "project_type": project.project_type if project else "Unknown",
        "estimate_type": project.estimate_type if project else "Unknown",
        "total_items": item_count,
        "total_amount": round(total_amount, 2),
        "unpriced_items": unpriced_items,
        "pricing_complete": unpriced_items == 0,
        "items_count_by_category": _count_by_category(boq),
    }


def _count_by_category(boq):
    """Count BOQ items by work category."""
    from collections import Counter
    categories = [item.get("work_category", "Other") for item in boq]
    return dict(Counter(categories))


@router.get("/{project_id}/export-excel")
def export_boq_excel(project_id: int, db: Session = Depends(get_db)):
    result = generate_boq_for_project(db, project_id)
    boq = result.get("boq")
    materials = result.get("materials")
    labour = result.get("labour")
    
    from backend.models.project import Project
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    summary = {
        "project_name": project.name if project else f"Project {project_id}",
        "project_type": project.project_type if project else "Unknown",
        "estimate_type": project.estimate_type if project else "Unknown",
        "client": project.client if project else "Unknown",
        "location": project.location if project else "Unknown",
    }
    content = boq_to_excel_bytes(boq, project_summary=summary, material_statement=materials, labour_statement=labour)
    return Response(content, media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", headers={"Content-Disposition": f"attachment; filename=boq_project_{project_id}.xlsx"})
