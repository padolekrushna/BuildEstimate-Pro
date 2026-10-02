from fastapi import FastAPI
from backend.api import projects, dsr, boq
from backend.database import Base, engine
from backend.models.project import Project
from backend.models.room import Room
from backend.models.opening import Opening
from backend.models.dsr_item import DSRItem
from backend.models.dsr_material import DSRMaterial
from backend.models.dsr_labour import DSRLabour
from backend.models.estimate_run import EstimateRun
from sqlalchemy import inspect, text


def create_app() -> FastAPI:
    app = FastAPI(title="BuildEstimate Pro - API")
    app.include_router(projects.router, prefix="/projects", tags=["projects"])
    app.include_router(dsr.router, prefix="/dsr", tags=["dsr"])
    app.include_router(boq.router, prefix="/projects", tags=["boq"])
    # ingestion & semantic search
    from backend.api.dsr_ingest import router as dsr_ingest_router
    app.include_router(dsr_ingest_router, prefix="/dsr", tags=["dsr-ingest"])
    return app


app = create_app()


@app.on_event("startup")
def on_startup():
    # create tables (for prototype)
    Base.metadata.create_all(bind=engine)
    if "context_json" not in {column["name"] for column in inspect(engine).get_columns("projects")}:
        with engine.begin() as connection:
            connection.execute(text("ALTER TABLE projects ADD COLUMN context_json TEXT"))
    room_columns = {column["name"] for column in inspect(engine).get_columns("rooms")}
    with engine.begin() as connection:
        if "count" not in room_columns:
            connection.execute(text("ALTER TABLE rooms ADD COLUMN count FLOAT NOT NULL DEFAULT 1"))
        if "details_json" not in room_columns:
            connection.execute(text("ALTER TABLE rooms ADD COLUMN details_json TEXT"))
