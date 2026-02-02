from typing import List, Any, Optional
from pydantic import BaseModel
from app.models.flood_risk import FloodZone
from app.models.placement import PlacementSuggestion, BuildabilityResult


class FloodZoneResponse(BaseModel):
    type: str = "FeatureCollection"
    features: List[Any] = []

    @classmethod
    def from_domain(cls, zones: FloodZone) -> "FloodZoneResponse":
        return cls(type=zones.type, features=zones.features)


class PlacementSuggestionsResponse(BaseModel):
    suggestions: List[dict]

    @classmethod
    def from_domain(cls, suggestions: List[PlacementSuggestion]) -> "PlacementSuggestionsResponse":
        return cls(
            suggestions=[s.to_dict() for s in suggestions]
        )


class BuildabilityResponse(BaseModel):
    can_build: bool
    reasons: List[str]
    risk_factors: Optional[dict] = None

    @classmethod
    def from_domain(cls, result: BuildabilityResult) -> "BuildabilityResponse":
        return cls(
            can_build=result.can_build,
            reasons=result.reasons,
            risk_factors=result.risk_factors,
        )
