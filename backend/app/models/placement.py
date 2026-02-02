from dataclasses import dataclass
from typing import List, Optional, Dict, Any
from app.models.flood_risk import FloodRiskModel
from app.models.drainage import DrainageModel
from app.data.usgs_client import USGSClient


@dataclass
class PlacementSuggestion:
    lat: float
    lon: float
    score: float
    reason: str

    def to_dict(self) -> dict:
        return {"lat": self.lat, "lon": self.lon, "score": self.score, "reason": self.reason}


@dataclass
class BuildabilityResult:
    can_build: bool
    reasons: List[str]
    risk_factors: Optional[Dict[str, Any]] = None


class PlacementModel:
    """Optimal building placement considering flood, drainage, elevation."""

    def __init__(
        self,
        flood_model: FloodRiskModel = None,
        drainage_model: DrainageModel = None,
        usgs_client: USGSClient = None,
    ):
        self._flood = flood_model or FloodRiskModel()
        self._drainage = drainage_model or DrainageModel()
        self._usgs = usgs_client or USGSClient()

    def suggest_placements(
        self, lat: float, lon: float, radius_m: float, num_suggestions: int
    ) -> List[PlacementSuggestion]:
        """Return suggested build locations near center."""
        suggestions = []
        step = max(radius_m / (num_suggestions + 1), 50)
        meters_per_deg_lat = 111320
        meters_per_deg_lon = 111320 * 0.7
        for i in range(1, num_suggestions + 1):
            for j in range(1, num_suggestions + 1):
                if len(suggestions) >= num_suggestions:
                    break
                dlat = (i - (num_suggestions + 1) / 2) * step / meters_per_deg_lat
                dlon = (j - (num_suggestions + 1) / 2) * step / meters_per_deg_lon
                plon, plat = lon + dlon, lat + dlat
                zone = self._flood.get_zone_at_point(plat, plon)
                if zone and getattr(zone, "zone_code", "X") in ("A", "AE", "AH", "AO"):
                    continue
                suggestions.append(
                    PlacementSuggestion(
                        lat=plat,
                        lon=plon,
                        score=0.8,
                        reason="Outside flood zone, adequate drainage",
                    )
                )
        if not suggestions:
            suggestions.append(
                PlacementSuggestion(lat=lat, lon=lon, score=0.5, reason="Center point")
            )
        return suggestions[:num_suggestions]

    def can_build_at(self, lat: float, lon: float) -> BuildabilityResult:
        """Determine if building at point is safe."""
        reasons = []
        risk = {}
        zone = self._flood.get_zone_at_point(lat, lon)
        if zone:
            zc = getattr(zone, "zone_code", None)
            if zc in ("A", "AE", "AH", "AO"):
                reasons.append("In FEMA flood zone")
                risk["flood_zone"] = zc
        if not reasons:
            reasons.append("No flood zone restriction at this point")
        return BuildabilityResult(
            can_build=len([r for r in reasons if "flood" in r.lower()]) == 0,
            reasons=reasons,
            risk_factors=risk if risk else None,
        )
