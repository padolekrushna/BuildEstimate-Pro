from sqlalchemy import Column, Integer, String, Float, ForeignKey
from sqlalchemy.orm import relationship
from backend.models.base import Base


class Opening(Base):
    __tablename__ = "openings"
    id = Column(Integer, primary_key=True, index=True)
    room_id = Column(Integer, ForeignKey("rooms.id"), nullable=False)
    type = Column(String, nullable=False)  # e.g., door, window, ventilator
    width = Column(Float, nullable=False, default=0.0)
    height = Column(Float, nullable=False, default=0.0)
    count = Column(Integer, nullable=False, default=1)

    room = relationship("Room", backref="openings")

    @property
    def area(self) -> float:
        return (self.width or 0.0) * (self.height or 0.0) * (self.count or 1)
