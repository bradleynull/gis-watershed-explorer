from typing import List, Any
from pydantic import BaseModel
from app.models.elevation import Contours


class ContourResponse(BaseModel):
    type: str = "FeatureCollection"
    features: List[Any] = []

    @classmethod
    def from_domain(cls, contours: Contours) -> "ContourResponse":
        return cls(type=contours.type, features=contours.features)
