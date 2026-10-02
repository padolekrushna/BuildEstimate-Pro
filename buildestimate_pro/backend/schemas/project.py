from pydantic import BaseModel
from typing import Optional, List, Dict, Any


class ProjectCreate(BaseModel):
    name: str
    client: Optional[str] = None
    location: Optional[str] = None
    district: Optional[str] = None
    state: Optional[str] = None
    project_type: Optional[str] = "New Building"
    estimate_type: Optional[str] = "Repair & Maintenance"
    existing_building_type: Optional[str] = None
    number_of_floors: Optional[str] = None
    dsr_year: Optional[str] = None
    department: Optional[str] = None
    estimate_date: Optional[str] = None
    building_type: Optional[str] = None
    plan_file_name: Optional[str] = None
    context: Optional[Dict[str, Any]] = None


class ProjectOut(BaseModel):
    id: int
    name: str
    client: Optional[str]
    location: Optional[str]
    district: Optional[str] = None
    state: Optional[str] = None
    project_type: Optional[str] = "New Building"
    estimate_type: Optional[str] = "Repair & Maintenance"
    existing_building_type: Optional[str] = None
    number_of_floors: Optional[str] = None
    dsr_year: Optional[str] = None
    department: Optional[str] = None
    estimate_date: Optional[str] = None
    building_type: Optional[str] = None
    plan_file_name: Optional[str] = None

    class Config:
        orm_mode = True
