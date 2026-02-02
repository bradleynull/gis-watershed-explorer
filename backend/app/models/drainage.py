from dataclasses import dataclass
from typing import List, Any
from app.data.usgs_client import USGSClient
from app.core.geo_utils import bbox_from_center
import numpy as np


@dataclass
class FlowPath:
    geometry: dict
    properties: dict

    def __post_init__(self):
        if self.geometry is None:
            self.geometry = {"type": "LineString", "coordinates": []}
        if self.properties is None:
            self.properties = {"distance_m": 0, "reaches_stream": False}


class DrainageModel:
    """Pure business logic for water flow direction and accumulation."""

    def __init__(self, usgs_client: USGSClient = None):
        self._client = usgs_client or USGSClient()

    def calculate_flow_direction(self, lat: float, lon: float) -> FlowPath:
        """Calculate where water flows from a given point. Returns flow path as LineString."""
        dem = self._client.fetch_dem(lat, lon, 500)
        if dem is None:
            return FlowPath(
                geometry={"type": "LineString", "coordinates": [[lon, lat]]},
                properties={"distance_m": 0, "reaches_stream": False},
            )
        arr = np.array(dem.get("data", []))
        if arr.size == 0:
            return FlowPath(
                geometry={"type": "LineString", "coordinates": [[lon, lat]]},
                properties={"distance_m": 0, "reaches_stream": False},
            )
        transform = dem.get("transform", [])
        coords = self._trace_flow_path(arr, transform, lat, lon)
        dist_m = self._path_length_m(coords) if len(coords) > 1 else 0
        return FlowPath(
            geometry={"type": "LineString", "coordinates": coords},
            properties={"distance_m": round(dist_m, 2), "reaches_stream": False},
        )

    def _trace_flow_path(
        self, arr: np.ndarray, transform: list, lat: float, lon: float
    ) -> List[List[float]]:
        """Trace downhill from point; return list of [lon, lat]."""
        h, w = arr.shape
        nodata = -9999
        arr = np.where(arr == nodata, np.nan, arr)
        cell_width = transform[0] if len(transform) >= 1 else 0.0001
        cell_height = -transform[4] if len(transform) >= 5 else 0.0001
        lon_ul, lat_ul = transform[2], transform[5]
        col = (lon - lon_ul) / cell_width if cell_width else 0
        row = (lat_ul - lat) / cell_height if cell_height else 0
        col, row = int(np.clip(col, 0, w - 1)), int(np.clip(row, 0, h - 1))
        path = []
        max_steps = 500
        for _ in range(max_steps):
            lon_p = lon_ul + col * cell_width
            lat_p = lat_ul - row * cell_height
            path.append([round(lon_p, 6), round(lat_p, 6)])
            val = arr[row, col]
            if np.isnan(val):
                break
            best = None
            best_val = val
            for di, dj in [(-1, 0), (1, 0), (0, -1), (0, 1), (-1, -1), (-1, 1), (1, -1), (1, 1)]:
                ni, nj = row + di, col + dj
                if 0 <= ni < h and 0 <= nj < w:
                    nv = arr[ni, nj]
                    if not np.isnan(nv) and nv < best_val:
                        best_val = nv
                        best = (ni, nj)
            if best is None:
                break
            row, col = best
        return path

    def _path_length_m(self, coords: List[List[float]]) -> float:
        from math import radians, sin, cos, sqrt, atan2
        R = 6371000
        total = 0
        for i in range(len(coords) - 1):
            lon1, lat1 = coords[i][0], coords[i][1]
            lon2, lat2 = coords[i + 1][0], coords[i + 1][1]
            phi1, phi2 = radians(lat1), radians(lat2)
            dphi = radians(lat2 - lat1)
            dlam = radians(lon2 - lon1)
            a = sin(dphi / 2) ** 2 + cos(phi1) * cos(phi2) * sin(dlam / 2) ** 2
            c = 2 * atan2(sqrt(a), sqrt(1 - a))
            total += R * c
        return total
