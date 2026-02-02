import httpx
from typing import List, Dict, Any
from app.core.config import settings


class NHDClient:
    """Fetch rivers/streams from National Hydrography Dataset."""

    def __init__(self, base_url: str = None):
        self.base_url = base_url or settings.nhd_base_url

    def get_rivers_geojson(
        self, minx: float, miny: float, maxx: float, maxy: float
    ) -> Dict[str, Any]:
        """Return GeoJSON FeatureCollection of rivers/streams in bbox (WGS84)."""
        try:
            bbox = f"{minx},{miny},{maxx},{maxy}"
            url = f"{self.base_url}/nhd/MapServer/0/query"
            params = {
                "where": "1=1",
                "outFields": "*",
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
