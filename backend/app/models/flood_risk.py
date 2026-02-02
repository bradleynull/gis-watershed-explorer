from dataclasses import dataclass
from typing import List, Any, Optional
from app.data.fema_client import FEMAClient


@dataclass
class FloodZone:
    type: str = "FeatureCollection"
    features: List[Any] = None

    def __post_init__(self):
        if self.features is None:
            self.features = []


class FloodRiskModel:
    """Flood zone analysis using FEMA data."""

    def __init__(self, fema_client: FEMAClient = None):
        self._client = fema_client or FEMAClient()

    def get_flood_zones(
        self, minx: float, miny: float, maxx: float, maxy: float
    ) -> FloodZone:
        fc = self._client.get_flood_zones_geojson(minx, miny, maxx, maxy)
        return FloodZone(
            type=fc.get("type", "FeatureCollection"),
            features=fc.get("features", []),
        )

    def get_zone_at_point(self, lat: float, lon: float) -> Optional[Any]:
        """Return zone info at point. Returns object with zone_code, description or None."""
        props = self._client.get_zone_at_point(lat, lon)
        if props is None:
            return None
        zone_code = (props.get("FLD_ZONE") or props.get("ZONE") or "X")
        desc = {
            "A": "100-year flood zone",
            "AE": "100-year flood zone with BFE",
            "AH": "100-year shallow flooding",
            "AO": "100-year sheet flow",
            "X": "Area of minimal flood hazard",
        }.get(zone_code, str(zone_code))
        return _FloodZoneInfo(zone_code=zone_code, description=desc)


class _FloodZoneInfo:
    def __init__(self, zone_code: str, description: str):
        self.zone_code = zone_code
        self.description = description
