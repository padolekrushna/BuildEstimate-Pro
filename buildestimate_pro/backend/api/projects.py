import json
from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from backend.database import get_db
from backend.schemas.project import ProjectCreate, ProjectOut
from backend.models.project import Project
from backend.models.estimate_run import EstimateRun
from backend.models.room import Room
from backend.services.boq_engine import generate_boq_for_project

router = APIRouter()


@router.post("/", response_model=ProjectOut)
def create_project(payload: ProjectCreate, db: Session = Depends(get_db)):
    proj = Project(
        name=payload.name,
        client=payload.client,
        location=payload.location,
        district=payload.district,
        state=payload.state,
        project_type=payload.project_type or "New Building",
        estimate_type=payload.estimate_type or "Repair & Maintenance",
        existing_building_type=payload.existing_building_type,
        number_of_floors=payload.number_of_floors,
        dsr_year=payload.dsr_year,
        department=payload.department,
        estimate_date=payload.estimate_date,
        building_type=payload.building_type,
        plan_file_name=payload.plan_file_name,
        context_json=json.dumps(payload.context or {}),
    )
    db.add(proj)
    db.commit()
    db.refresh(proj)
    return proj


@router.get("/", response_model=list[ProjectOut])
def list_projects(db: Session = Depends(get_db)):
    return db.query(Project).order_by(Project.id.desc()).all()


@router.get("/history/all")
def list_project_history(db: Session = Depends(get_db)):
    projects = db.query(Project).order_by(Project.id.desc()).all()
    result = []
    for project in projects:
        last_run = db.query(EstimateRun).filter(EstimateRun.project_id == project.id).order_by(EstimateRun.created_at.desc()).first()
        result.append({
            "project_id": project.id,
            "project_name": project.name,
            "estimate_type": project.estimate_type,
            "created_at": project.created_at,
            "last_run": {
                "id": last_run.id,
                "status": last_run.status,
                "total_amount": last_run.total_amount,
                "item_count": last_run.item_count,
                "created_at": last_run.created_at,
            } if last_run else None,
        })
    return result


@router.get("/{project_id}/history")
def get_project_history(project_id: int, db: Session = Depends(get_db)):
    if not db.query(Project).filter(Project.id == project_id).first():
        raise HTTPException(status_code=404, detail="Project not found")
    runs = db.query(EstimateRun).filter(EstimateRun.project_id == project_id).order_by(EstimateRun.created_at.desc()).all()
    return [{"id": run.id, "status": run.status, "total_amount": run.total_amount, "item_count": run.item_count, "created_at": run.created_at, "boq": json.loads(run.boq_json)} for run in runs]


@router.post("/{project_id}/runs")
def create_estimate_run(project_id: int, db: Session = Depends(get_db)):
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    result = generate_boq_for_project(db, project_id)
    boq = result.get("boq", [])
    approvals = json.loads(project.context_json or "{}").get("dsr_approvals", {})
    unapproved = [item.get("dsr_item_no") for item in boq if item.get("dsr_item_no") and item.get("dsr_approval_required") and not approvals.get(str(item.get("dsr_item_no")), False)]
    if unapproved:
        raise HTTPException(status_code=409, detail={"message": "Approve uncertain DSR matches before creating an estimate run", "items": unapproved})
    rooms = db.query(Room).filter(Room.project_id == project_id).all()
    run = EstimateRun(
        project_id=project_id,
        status="completed" if all(item.get("amount") is not None for item in boq) else "completed_with_unpriced_items",
        total_amount=round(sum(item.get("amount") or 0 for item in boq), 2),
        item_count=len(boq),
        boq_json=json.dumps(boq, default=str),
        measurements_json=json.dumps([
            {
                "name": room.name,
                "length": room.length,
                "width": room.width,
                "height": room.height,
                "count": room.count,
                "details": json.loads(room.details_json or "{}"),
                "openings": [
                    {"type": opening.type, "width": opening.width, "height": opening.height, "count": opening.count}
                    for opening in room.openings
                ],
            }
            for room in rooms
        ]),
    )
    db.add(run)
    db.commit()
    db.refresh(run)
    return {"id": run.id, "project_id": project_id, "status": run.status, "total_amount": run.total_amount, "item_count": run.item_count, "created_at": run.created_at}


@router.post("/{project_id}/dsr-approvals")
async def save_dsr_approvals(project_id: int, request: Request, db: Session = Depends(get_db)):
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    payload = await request.json()
    approvals = payload.get("approvals", {}) if isinstance(payload, dict) else {}
    context = json.loads(project.context_json or "{}")
    context["dsr_approvals"] = {str(key): bool(value) for key, value in approvals.items()}
    project.context_json = json.dumps(context)
    db.commit()
    return {"project_id": project_id, "approvals": context["dsr_approvals"]}


@router.get("/{project_id}", response_model=ProjectOut)
def get_project(project_id: int, db: Session = Depends(get_db)):
    proj = db.query(Project).filter(Project.id == project_id).first()
    if not proj:
        raise HTTPException(status_code=404, detail="Project not found")
    return proj


@router.post("/{project_id}/rooms", response_model=dict)
async def save_rooms(project_id: int, request: Request, db: Session = Depends(get_db)):
    """Save multiple rooms for a project, replacing existing ones.

    Accepts either a raw JSON list or a wrapped object like {"rooms_data": [...]}.
    """
    from backend.models.room import Room
    from backend.models.opening import Opening

    payload = await request.json()
    rooms_data = payload.get("rooms_data", payload) if isinstance(payload, dict) else payload
    if not db.query(Project).filter(Project.id == project_id).first():
        raise HTTPException(status_code=404, detail="Project not found")
    if not isinstance(rooms_data, list) or not rooms_data:
        raise HTTPException(status_code=422, detail="rooms_data must be a list of room objects")

    normalized = []
    for index, room_info in enumerate(rooms_data, start=1):
        try:
            name = str(room_info.get("name") or room_info.get("Room") or room_info.get("Component") or "").strip()
            length = float(room_info.get("length") or room_info.get("Length_m") or 0.0)
            width = float(room_info.get("width") or room_info.get("Width_m") or 0.0)
            height = float(room_info.get("height") or room_info.get("Height_m") or 3.0)
            count = float(room_info.get("count", room_info.get("Count", 1)) or 0)
            details = room_info.get("details", {}) or {}
            if not isinstance(details, dict):
                raise ValueError("details must be an object")
            if not name or min(length, width, height, count) <= 0:
                raise ValueError("name and positive dimensions are required")
            numeric_details = {key: float(value) for key, value in details.items()}
            if any(value < 0 for value in numeric_details.values()):
                raise ValueError("detail measurements cannot be negative")
            openings = []
            for opening_info in room_info.get("openings", []):
                opening_type = str(opening_info.get("type") or "").lower()
                if opening_type not in {"door", "window", "ventilator"}:
                    raise ValueError("opening type must be door, window, or ventilator")
                opening_width = float(opening_info.get("width") or 0.0)
                opening_height = float(opening_info.get("height") or 0.0)
                opening_count = int(opening_info.get("count") or 1)
                if min(opening_width, opening_height, opening_count) <= 0:
                    raise ValueError("opening dimensions and count must be positive")
                openings.append((opening_type, opening_width, opening_height, opening_count))
            normalized.append((name, length, width, height, count, numeric_details, openings))
        except (TypeError, ValueError) as exc:
            raise HTTPException(status_code=422, detail=f"Invalid room {index}: {exc}")

    db.query(Room).filter(Room.project_id == project_id).delete()
    for name, length, width, height, count, details, openings in normalized:
        room = Room(project_id=project_id, name=name, length=length, width=width, height=height, count=count, details_json=json.dumps(details))
        db.add(room)
        db.flush()
        for opening_type, opening_width, opening_height, opening_count in openings:
            db.add(Opening(room_id=room.id, type=opening_type, width=opening_width, height=opening_height, count=opening_count))
    db.commit()
    return {"message": f"Saved {len(rooms_data)} rooms for project {project_id}"}


@router.get("/{project_id}/rooms")
def get_project_rooms(project_id: int, db: Session = Depends(get_db)):
    """Fetch all rooms for a project."""
    from backend.models.room import Room
    
    rooms = db.query(Room).filter(Room.project_id == project_id).all()
    return [
        {
            "id": r.id,
            "name": r.name,
            "length": r.length,
            "width": r.width,
            "height": r.height,
            "count": r.count,
            "details": json.loads(r.details_json or "{}"),
            "area": r.area,
            "openings": [
                {
                    "id": o.id,
                    "type": o.type,
                    "width": o.width,
                    "height": o.height,
                    "count": o.count,
                }
                for o in getattr(r, "openings", [])
            ],
        }
        for r in rooms
    ]
