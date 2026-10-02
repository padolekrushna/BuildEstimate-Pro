from sqlalchemy import Column, Integer, String, Float, Text
from backend.models.base import Base


class DSRItem(Base):
    __tablename__ = "dsr_items"
    id = Column(Integer, primary_key=True, index=True)
    item_no = Column(String, nullable=True, index=True)
    chapter = Column(String, nullable=True)
    description = Column(Text, nullable=False)
    unit = Column(String, nullable=True)
    rate = Column(Float, nullable=True)
    source = Column(String, nullable=True)
    page = Column(Integer, nullable=True)
