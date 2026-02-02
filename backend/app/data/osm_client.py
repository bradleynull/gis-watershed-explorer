import httpx
from typing import Dict, Any
from app.core.config import settings


class OSMClient:
    """Fetch structures/buildings from OpenStreetMap."""

    def __init__(self, base_url: str = None):
        self.base_url = base_url or settings.osm_base_url

    def get_structures_geojson(
        self, minx: float, miny: float, maxx: float, maxy: float
    ) -> Dict[str, Any]:
        """Return GeoJSON of buildings in bbox (WGS84). Uses Overpass API."""
        try:
            overpass = "https://overpass-api.de/api/interpreter"
            query = f"""
            [out:json][timeout:25];
            (
              way["building"]({miny},{minx},{maxy},{maxx});
            );
            out body;
            >;
            out skel qt;
            """
            with httpx.Client(timeout=25.0) as client:
                r = client.post(overpass, data={"data": query})
                if r.status_code != 200:
                    return {"type": "FeatureCollection", "features": []}
                data = r.json()
            from app.core.overpass_to_geojson import overpass_to_geojson
            return overpass_to_geojson(data)
        except Exception:
            return {"type": "FeatureCollection", "features": []}
