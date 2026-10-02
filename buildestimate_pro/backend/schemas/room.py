from pydantic import BaseModel
from typing import Optional


class RoomCreate(BaseModel):
    project_id: int
    name: str
    length: float
    width: float
    height: Optional[float] = 3.0


class RoomOut(BaseModel):
    id: int
    project_id: int
    name: str
    length: float
    width: float
    height: float
    area: float

    class Config:
        orm_mode = True
