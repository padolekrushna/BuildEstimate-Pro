from sqlalchemy import Column, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.sql import func
from backend.models.base import Base


class EstimateRun(Base):
    __tablename__ = "estimate_runs"

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False, index=True)
    status = Column(String, nullable=False, default="completed")
    total_amount = Column(Float, nullable=False, default=0.0)
    item_count = Column(Integer, nullable=False, default=0)
    boq_json = Column(Text, nullable=False, default="[]")
    measurements_json = Column(Text, nullable=False, default="[]")
    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)