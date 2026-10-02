from sqlalchemy import Column, Integer, String, Float, ForeignKey, Text
from sqlalchemy.orm import relationship
from backend.models.base import Base


class Room(Base):
    __tablename__ = "rooms"
    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False)
    name = Column(String, nullable=False)
    length = Column(Float, nullable=False, default=0.0)
    width = Column(Float, nullable=False, default=0.0)
    height = Column(Float, nullable=False, default=3.0)
    count = Column(Float, nullable=False, default=1.0)
    details_json = Column(Text, nullable=True)

    project = relationship("Project", backref="rooms")

    @property
    def area(self) -> float:
        return (self.length or 0.0) * (self.width or 0.0)

    def total_openings_area(self) -> float:
        return sum((o.area for o in getattr(self, "openings", [])))

