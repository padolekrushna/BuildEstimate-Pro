from pydantic import BaseModel
from typing import Optional


class OpeningCreate(BaseModel):
    room_id: int
    type: str
    width: float
    height: float
    count: Optional[int] = 1


class OpeningOut(BaseModel):
    id: int
    room_id: int
    type: str
    width: float
    height: float
    count: int
    area: float

    class Config:
        orm_mode = True
