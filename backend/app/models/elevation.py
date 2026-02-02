from dataclasses import dataclass
from typing import List, Any
from app.data.usgs_client import USGSClient


@dataclass
class Contours:
    type: str = "FeatureCollection"
    features: List[Any] = None

    def __post_init__(self):
        if self.features is None:
            self.features = []


class ElevationModel:
    """Pure business logic for elevation and contour processing."""

    def __init__(self, usgs_client: USGSClient = None):
        self._client = usgs_client or USGSClient()

    def get_contours(self, lat: float, lon: float, radius_m: float, interval_m: float) -> Contours:
        dem_data = self._client.fetch_dem(lat, lon, radius_m)
        if dem_data is None:
            return Contours(features=[])
        return self._generate_contours(dem_data, interval_m)

    def get_contours_for_bbox(
        self, minx: float, miny: float, maxx: float, maxy: float, interval_m: float = 5.0
    ) -> Contours:
        """Generate contours for a bounding box (lon, lat) with jet_value for colormap."""
        import math
        from app.core.geo_utils import meters_per_degree_lat, meters_per_degree_lon

        center_lon = (minx + maxx) / 2.0
        center_lat = (miny + maxy) / 2.0
        # Radius to cover bbox: half the diagonal in meters
        dlat_deg = maxy - miny
        dlon_deg = maxx - minx
        m_per_deg_lat = meters_per_degree_lat(center_lat)
        m_per_deg_lon = meters_per_degree_lon(center_lat)
        half_width_m = (dlon_deg * m_per_deg_lon) / 2.0
        half_height_m = (dlat_deg * m_per_deg_lat) / 2.0
        radius_m = math.sqrt(half_width_m ** 2 + half_height_m ** 2) * 1.1  # slight margin

        dem_data = self._client.fetch_dem(center_lat, center_lon, radius_m)
        if dem_data is None:
            return Contours(features=[])
        
        contours = self._generate_contours_with_jet(dem_data, interval_m)
        
        # Clip contours to the requested bbox
        clipped_features = []
        for feature in contours.features:
            coords = feature.get("geometry", {}).get("coordinates", [])
            # Filter coordinates to only those within bbox
            clipped_coords = [
                [x, y] for x, y in coords
                if minx <= x <= maxx and miny <= y <= maxy
            ]
            # Only include if we have at least 2 points (valid line)
            if len(clipped_coords) >= 2:
                clipped_feature = {
                    "type": "Feature",
                    "geometry": {"type": "LineString", "coordinates": clipped_coords},
                    "properties": feature.get("properties", {}),
                }
                clipped_features.append(clipped_feature)
        
        return Contours(features=clipped_features)

    def _generate_contours(self, dem_data: dict, interval_m: float) -> Contours:
        import numpy as np
        from affine import Affine
        data = dem_data.get("data")
        transform = dem_data.get("transform")
        if data is None or transform is None:
            return Contours(features=[])
        arr = np.array(data)
        if arr.size == 0:
            return Contours(features=[])
        nodata = dem_data.get("nodata", -9999)
        arr = np.where(arr == nodata, np.nan, arr)
        valid = np.nanmin(arr), np.nanmax(arr)
        if np.isnan(valid[0]) or np.isnan(valid[1]):
            return Contours(features=[])
        min_elev = int(np.nanmin(arr) // interval_m) * interval_m
        max_elev = int(np.nanmax(arr) // interval_m + 1) * interval_m
        levels = np.arange(min_elev, max_elev + interval_m, interval_m)
        features = []
        aff = Affine(*transform) if isinstance(transform, (list, tuple)) else transform
        for level in levels:
            from skimage import measure
            try:
                contours = measure.find_contours(arr, level)
            except Exception:
                continue
            for contour in contours:
                if len(contour) < 3:
                    continue
                coords = []
                for row, col in contour:
                    x, y = aff * (col, row)
                    coords.append([float(x), float(y)])
                coords.append(coords[0])
                features.append({
                    "type": "Feature",
                    "geometry": {"type": "LineString", "coordinates": coords},
                    "properties": {"elevation": float(level)},
                })
        return Contours(features=features)

    def _generate_contours_with_jet(self, dem_data: dict, interval_m: float) -> Contours:
        """Generate contours with jet_value (0-1) for colormap."""
        import numpy as np
        from affine import Affine
        from skimage import measure

        data = dem_data.get("data")
        transform = dem_data.get("transform")
        if data is None or transform is None:
            return Contours(features=[])
        arr = np.array(data)
        if arr.size == 0:
            return Contours(features=[])
        nodata = dem_data.get("nodata", -9999)
        arr = np.where(arr == nodata, np.nan, arr)
        valid_min, valid_max = np.nanmin(arr), np.nanmax(arr)
        if np.isnan(valid_min) or np.isnan(valid_max):
            return Contours(features=[])
        min_elev = float(valid_min)
        max_elev = float(valid_max)
        elev_range = max_elev - min_elev if max_elev > min_elev else 1.0

        start_level = int(min_elev // interval_m) * interval_m
        end_level = int(max_elev // interval_m + 1) * interval_m
        levels = np.arange(start_level, end_level + interval_m, interval_m)

        features = []
        aff = Affine(*transform) if isinstance(transform, (list, tuple)) else transform
        for level in levels:
            if level < min_elev or level > max_elev:
                continue
            try:
                contour_list = measure.find_contours(arr, level)
            except Exception:
                continue
            for contour in contour_list:
                if len(contour) < 3:
                    continue
                coords = []
                for row, col in contour:
                    x, y = aff * (col, row)
                    coords.append([float(x), float(y)])
                if len(coords) < 2:
                    continue
                jet_value = float((level - min_elev) / elev_range)
                features.append({
                    "type": "Feature",
                    "geometry": {"type": "LineString", "coordinates": coords},
                    "properties": {
                        "elevation": float(level),
                        "jet_value": round(jet_value, 4),
                    },
                })
        return Contours(features=features)
