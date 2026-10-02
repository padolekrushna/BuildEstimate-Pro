from sqlalchemy import Column, Integer, String, Float, ForeignKey
from sqlalchemy.orm import relationship
from backend.models.base import Base


class DSRLabour(Base):
    __tablename__ = "dsr_labour"
    id = Column(Integer, primary_key=True, index=True)
    dsr_item_id = Column(Integer, ForeignKey("dsr_items.id"), nullable=False)
    labour_type = Column(String, nullable=False)
    quantity = Column(Float, nullable=True)
    unit = Column(String, nullable=True)

    dsr_item = relationship("DSRItem", backref="labour")
