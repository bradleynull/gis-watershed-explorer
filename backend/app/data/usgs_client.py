import httpx
import numpy as np
import io
import logging
from typing import Optional, Dict, Any
from app.core.config import settings
from app.core.geo_utils import bbox_from_center, latlon_to_web_mercator

logger = logging.getLogger(__name__)


class USGSClient:
    """Fetch elevation/DEM data from USGS 3DEP."""

    def __init__(self, base_url: str = None):
        self.base_url = base_url or settings.usgs_base_url

    def fetch_dem(
        self, lat: float, lon: float, radius_m: float
    ) -> Optional[Dict[str, Any]]:
        """Fetch DEM data for area around lat, lon. Returns dict with 'data' (2D array), 'transform', 'nodata'."""
        try:
            minx, miny, maxx, maxy = bbox_from_center(lat, lon, radius_m)
            x1, y1 = latlon_to_web_mercator(miny, minx)
            x2, y2 = latlon_to_web_mercator(maxy, maxx)
            extent = f"{x1},{y1},{x2},{y2}"
            # Use 3DEPElevation/ImageServer (correct path per USGS docs)
            url = f"{self.base_url}/3DEPElevation/ImageServer/exportImage"
            params = {
                "bbox": extent,
                "bboxSR": "3857",  # Web Mercator
                "imageSR": "4326",  # Request output in WGS84
                "size": "100,100",
                "format": "tiff",
                "pixelType": "F32",
                "f": "json",
            }
            with httpx.Client(timeout=30.0) as client:
                r = client.get(url, params=params)
                if r.status_code != 200:
                    logger.warning(f"USGS API returned {r.status_code}, using synthetic DEM")
                    return self._synthetic_dem(lat, lon, radius_m)
                data = r.json()
                if "href" not in data:
                    logger.warning("USGS response missing 'href', using synthetic DEM")
                    return self._synthetic_dem(lat, lon, radius_m)
                # Fetch the actual TIFF
                tiff_url = data["href"]
                with httpx.Client(timeout=30.0) as img_client:
                    img_r = img_client.get(tiff_url)
                    if img_r.status_code != 200:
                        logger.warning(f"TIFF fetch returned {img_r.status_code}, using synthetic DEM")
                        return self._synthetic_dem(lat, lon, radius_m)
                    # Parse TIFF with rasterio
                    return self._parse_tiff(img_r.content, lat, lon, radius_m, minx, miny, maxx, maxy)
        except Exception as e:
            logger.warning(f"Error fetching DEM: {e}, using synthetic DEM")
            return self._synthetic_dem(lat, lon, radius_m)

    def _parse_tiff(
        self, tiff_bytes: bytes, lat: float, lon: float, radius_m: float,
        minx: float, miny: float, maxx: float, maxy: float
    ) -> Dict[str, Any]:
        """Parse TIFF bytes using rasterio and return elevation array + transform."""
        try:
            import rasterio
            from rasterio.io import MemoryFile

            with MemoryFile(tiff_bytes) as memfile:
                with memfile.open() as dataset:
                    arr = dataset.read(1)  # First band
                    nodata = dataset.nodata if dataset.nodata is not None else -9999
                    # Get transform (Affine) - convert to list for JSON serialization
                    t = dataset.transform
                    # Transform is Affine(a, b, c, d, e, f) -> [a, b, c, d, e, f]
                    # a = cell_width, e = -cell_height, c = lon_ul, f = lat_ul
                    transform = [t.a, t.b, t.c, t.d, t.e, t.f]
                    logger.info(f"Parsed TIFF: shape={arr.shape}, nodata={nodata}")
                    return {
                        "data": arr.tolist(),
                        "transform": transform,
                        "nodata": nodata,
                        "source": "usgs_3dep",
                    }
        except Exception as e:
            logger.warning(f"Error parsing TIFF: {e}, using synthetic DEM")
            return self._synthetic_dem(lat, lon, radius_m)

    def _synthetic_dem(self, lat: float, lon: float, radius_m: float) -> Dict[str, Any]:
        """Return synthetic DEM for testing when USGS is unavailable."""
        size = 50
        arr = np.zeros((size, size))
        cx, cy = size // 2, size // 2
        for i in range(size):
            for j in range(size):
                dist = np.sqrt((i - cx) ** 2 + (j - cy) ** 2) / cx
                arr[i, j] = 200 - dist * 50 + np.random.rand() * 5
        meters_per_deg_lat = 111320
        meters_per_deg_lon = 111320 * 0.7
        cell_width = (2 * radius_m) / size / meters_per_deg_lon
        cell_height = (2 * radius_m) / size / meters_per_deg_lat
        transform = [
            cell_width,
            0,
            lon - radius_m / meters_per_deg_lon,
            0,
            -cell_height,
            lat + radius_m / meters_per_deg_lat,
        ]
        return {
            "data": arr.tolist(),
            "transform": transform,
            "nodata": -9999,
        }
