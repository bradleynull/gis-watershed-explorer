import httpx
from typing import List, Dict, Any, Optional
from app.core.config import settings


class FEMAClient:
    """Fetch flood zone data from FEMA National Flood Hazard Layer."""

    def __init__(self, base_url: str = None):
        self.base_url = base_url or settings.fema_base_url

    def get_flood_zones_geojson(
        self, minx: float, miny: float, maxx: float, maxy: float
    ) -> Dict[str, Any]:
        """Return GeoJSON FeatureCollection of flood zones in bbox (WGS84)."""
        try:
            url = f"{self.base_url}/NFHL/MapServer/28/query"
            params = {
                "where": "1=1",
                "outFields": "FLD_ZONE,ZONE",
                "returnGeometry": "true",
                "outSR": "4326",
                "f": "geojson",
                "geometry": f'{{"xmin":{minx},"ymin":{miny},"xmax":{maxx},"ymax":{maxy},"spatialReference":{{"wkid":4326}}}}',
                "geometryType": "esriGeometryEnvelope",
            }
            with httpx.Client(timeout=15.0) as client:
                r = client.get(url, params=params)
                if r.status_code == 200:
                    return r.json()
        except Exception:
            pass
        return {"type": "FeatureCollection", "features": []}

    def get_zone_at_point(self, lat: float, lon: float) -> Optional[Dict[str, Any]]:
        """Return flood zone at point if any."""
        tol = 0.001
        fc = self.get_flood_zones_geojson(lon - tol, lat - tol, lon + tol, lat + tol)
        for f in fc.get("features", []):
            return f.get("properties", {})
        return None
