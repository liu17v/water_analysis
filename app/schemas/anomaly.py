from pydantic import BaseModel


class AnomalyItem(BaseModel):
    id: int
    lon: float
    lat: float
    depth: float
    indicator: str
    value: float
    method: str
