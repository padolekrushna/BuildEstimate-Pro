from sqlalchemy import Column, Integer, String, DateTime, Text
from sqlalchemy.sql import func
from backend.models.base import Base


class Project(Base):
    __tablename__ = "projects"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    client = Column(String, nullable=True)
    location = Column(String, nullable=True)
    district = Column(String, nullable=True)
    state = Column(String, nullable=True)
    project_type = Column(String, nullable=True, default="New Building")
    estimate_type = Column(String, nullable=True, default="Repair & Maintenance")
    existing_building_type = Column(String, nullable=True)
    number_of_floors = Column(String, nullable=True)
    dsr_year = Column(String, nullable=True)
    department = Column(String, nullable=True)
    estimate_date = Column(String, nullable=True)
    building_type = Column(String, nullable=True)
    plan_file_name = Column(String, nullable=True)
    context_json = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
