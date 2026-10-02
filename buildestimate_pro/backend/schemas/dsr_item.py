from pydantic import BaseModel
from typing import Optional


class DSRItemOut(BaseModel):
    id: int
    item_no: Optional[str]
    description: str
    unit: Optional[str]
    rate: Optional[float]
    source: Optional[str]
    page: Optional[int]

    class Config:
        orm_mode = True
