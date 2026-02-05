from dataclasses import dataclass
from typing import List, Any, Set, Tuple, Optional
import logging
from app.data.nhd_client import NHDClient
from app.core.geo_utils import bbox_from_center
import numpy as np
from app.data.usgs_client import USGSClient
from app.data.cesium_terrain_client import CesiumTerrainClient
from shapely.geometry import Polygon as ShapelyPolygon
from pyproj import Geod

logger = logging.getLogger(__name__)


# D8 flow direction encoding: 1=E, 2=SE, 3=S, 4=SW, 5=W, 6=NW, 7=N, 8=NE
# Row,col deltas for each direction (drow, dcol)
D8_OFFSETS = [
    (0, 1),   # 1 E
    (1, 1),   # 2 SE
    (1, 0),   # 3 S
    (1, -1),  # 4 SW
    (0, -1),  # 5 W
    (-1, -1), # 6 NW
    (-1, 0),  # 7 N
    (-1, 1),  # 8 NE
]

# Inverse: for direction d, which neighbors flow INTO this cell (their flow points to us)
# Neighbor at (r+dr, c+dc) flows into (r,c) if its flow direction points to (r,c)
def _inverse_d8() -> List[Tuple[int, int]]:
    # All 8 neighbors can potentially flow into us
    return [(-dr, -dc) for dr, dc in D8_OFFSETS]


@dataclass
class Rivers:
    type: str = "FeatureCollection"
    features: List[Any] = None

    def __post_init__(self):
        if self.features is None:
            self.features = []


@dataclass
class Watershed:
    geometry: dict
    properties: dict

    def __post_init__(self):
        if self.geometry is None:
            self.geometry = {"type": "Polygon", "coordinates": []}
        if self.properties is None:
            self.properties = {"area_ha": 0, "time_of_concentration_min": 0}


@dataclass
class WatershedContours:
    type: str = "FeatureCollection"
    features: List[Any] = None
    properties: dict = None

    def __post_init__(self):
        if self.features is None:
            self.features = []
        if self.properties is None:
            self.properties = {}


@dataclass
class WatershedGrid:
    features: List[dict]
    metadata: dict


class WatershedModel:
    """Watershed delineation and river data."""

    def __init__(
        self, 
        nhd_client: NHDClient = None, 
        usgs_client: USGSClient = None,
        cesium_client: CesiumTerrainClient = None
    ):
        self._nhd = nhd_client or NHDClient()
        self._usgs = usgs_client or USGSClient()
        self._cesium = cesium_client or CesiumTerrainClient()

    def get_rivers_in_bbox(
        self, minx: float, miny: float, maxx: float, maxy: float
    ) -> Rivers:
        fc = self._nhd.get_rivers_geojson(minx, miny, maxx, maxy)
        return Rivers(
            type=fc.get("type", "FeatureCollection"),
            features=fc.get("features", []),
        )

    def delineate_watershed(self, lat: float, lon: float, radius_m: float = 1500) -> Watershed:
        """Delineate watershed containing the clicked point. Traces downstream to find pour point, then upstream."""
        dem = self._usgs.fetch_dem(lat, lon, radius_m)
        if dem is None:
            return self._fallback_watershed(lat, lon)
        arr = np.array(dem.get("data", []))
        if arr.size == 0:
            return self._fallback_watershed(lat, lon)
        transform = dem.get("transform", [])
        nodata = dem.get("nodata", -9999)
        arr = np.where(arr == nodata, np.nan, arr)
        h, w = arr.shape
        cell_width = abs(transform[0]) if len(transform) >= 1 else 0.0001
        cell_height = abs(transform[4]) if len(transform) >= 5 else 0.0001
        lon_ul, lat_ul = transform[2], transform[5]
        # Starting cell (where user clicked)
        col = int(np.clip((lon - lon_ul) / cell_width, 0, w - 1))
        row = int(np.clip((lat_ul - lat) / cell_height, 0, h - 1))

        # D8 flow direction: flow_dirs[r,c] = 1..8 (direction of steepest descent), 0 = no flow
        flow_dirs = self._flow_direction_d8(arr)

        # Trace downstream from clicked point to find the pour point (outlet)
        outlet_r, outlet_c = self._trace_downstream(flow_dirs, row, col, h, w)

        # Watershed mask: all cells that drain to the pour point
        mask = self._drainage_basin(flow_dirs, outlet_r, outlet_c, h, w)
        if mask is None or np.sum(mask) < 3:
            return self._fallback_watershed(lat, lon)

        # Polygon from watershed boundary (convex hull of mask cells for simplicity)
        coords = self._mask_to_polygon(mask, lon_ul, lat_ul, cell_width, cell_height)
        if not coords:
            return self._fallback_watershed(lat, lon)

        # Area in hectares: geodesic area of polygon (WGS84)
        area_ha = self._geodesic_area_ha(coords)

        meters_per_deg_lat = 111320
        meters_per_deg_lon = 111320 * 0.707
        # Longest flow path L (m) and slope for time of concentration
        L_m, slope = self._longest_flow_path_and_slope(
            arr, flow_dirs, mask, outlet_r, outlet_c, cell_width, cell_height,
            meters_per_deg_lat, meters_per_deg_lon
        )
        tc_min = self._time_of_concentration_kirpich(L_m, slope)

        # Convert outlet cell back to lat/lon for response
        outlet_lon = lon_ul + (outlet_c + 0.5) * cell_width
        outlet_lat = lat_ul - (outlet_r + 0.5) * cell_height

        return Watershed(
            geometry={"type": "Polygon", "coordinates": [coords]},
            properties={
                "area_ha": round(area_ha, 2),
                "time_of_concentration_min": round(tc_min, 2),
                "outlet_lat": outlet_lat,
                "outlet_lon": outlet_lon,
                "longest_path_m": round(L_m, 2),
                "slope": round(slope, 4),
            },
        )

    def _trace_downstream(self, flow_dirs: np.ndarray, start_r: int, start_c: int, h: int, w: int) -> Tuple[int, int]:
        """Trace flow downstream from start cell until we hit edge, pit, or cycle. Returns pour point (outlet)."""
        r, c = start_r, start_c
        visited = set()
        visited.add((r, c))

        while True:
            d = flow_dirs[r, c]
            if d == 0:
                # No flow direction (flat or pit) - this is the outlet
                break
            dr, dc = D8_OFFSETS[d - 1]
            nr, nc = r + dr, c + dc
            # Check bounds
            if nr < 0 or nr >= h or nc < 0 or nc >= w:
                # Flow goes off edge - current cell is outlet
                break
            if (nr, nc) in visited:
                # Cycle detected - use current cell as outlet
                break
            visited.add((nr, nc))
            r, c = nr, nc

        return r, c

    def _flow_direction_d8(self, arr: np.ndarray) -> np.ndarray:
        """D8 flow direction grid: 1-8, 0 = no data or flat."""
        h, w = arr.shape
        flow = np.zeros((h, w), dtype=np.int32)
        for r in range(1, h - 1):
            for c in range(1, w - 1):
                z = arr[r, c]
                if np.isnan(z):
                    continue
                best_drop = 0
                best_dir = 0
                for idx, (dr, dc) in enumerate(D8_OFFSETS):
                    nr, nc = r + dr, c + dc
                    nz = arr[nr, nc]
                    if np.isnan(nz):
                        continue
                    drop = z - nz
                    if drop > best_drop:
                        best_drop = drop
                        best_dir = idx + 1
                flow[r, c] = best_dir
        return flow

    def _drainage_basin(self, flow_dirs: np.ndarray, outlet_r: int, outlet_c: int, h: int, w: int) -> np.ndarray:
        """All cells that drain to outlet. BFS from outlet following flow backwards (upstream)."""
        mask = np.zeros((h, w), dtype=bool)
        mask[outlet_r, outlet_c] = True
        queue: List[Tuple[int, int]] = [(outlet_r, outlet_c)]
        inv = _inverse_d8()
        while queue:
            r, c = queue.pop(0)
            for dr, dc in inv:
                nr, nc = r + dr, c + dc
                if nr < 0 or nr >= h or nc < 0 or nc >= w or mask[nr, nc]:
                    continue
                # Neighbor (nr,nc) flows toward (r,c) if its D8 points to (r,c)
                ndir = flow_dirs[nr, nc]
                if ndir == 0:
                    continue
                sr, sc = D8_OFFSETS[ndir - 1]
                if nr + sr == r and nc + sc == c:
                    mask[nr, nc] = True
                    queue.append((nr, nc))
        return mask

    def _mask_to_polygon(
        self, mask: np.ndarray, lon_ul: float, lat_ul: float, cell_width: float, cell_height: float
    ) -> List[List[float]]:
        """Convert watershed mask to polygon (boundary). Use convex hull of mask cell centers."""
        h, w = mask.shape
        points: List[Tuple[float, float]] = []
        for r in range(h):
            for c in range(w):
                if not mask[r, c]:
                    continue
                lon = lon_ul + (c + 0.5) * cell_width
                lat = lat_ul - (r + 0.5) * cell_height
                points.append((lon, lat))
        if len(points) < 3:
            return []
        # Convex hull (Graham scan or use boundary)
        hull = self._convex_hull(points)
        # Close ring
        hull.append(hull[0])
        return [[x, y] for x, y in hull]

    def _convex_hull(self, points: List[Tuple[float, float]]) -> List[Tuple[float, float]]:
        """Convex hull of points (lon, lat). Returns ordered boundary (no closing point)."""
        if len(points) <= 2:
            return list(points)
        points = sorted(set(points))
        start = min(points, key=lambda p: (p[1], p[0]))

        def polar_key(p):
            if p == start:
                return -999, -999
            dx = p[0] - start[0]
            dy = p[1] - start[1]
            return np.arctan2(dy, dx), (dx * dx + dy * dy)

        sorted_pts = sorted(points, key=polar_key)
        hull: List[Tuple[float, float]] = [sorted_pts[0], sorted_pts[1]]
        for i in range(2, len(sorted_pts)):
            p = sorted_pts[i]
            while len(hull) >= 2:
                a, b = hull[-2], hull[-1]
                cross = (b[0] - a[0]) * (p[1] - a[1]) - (b[1] - a[1]) * (p[0] - a[0])
                if cross <= 0:
                    hull.pop()
                else:
                    break
            hull.append(p)
        return hull

    def _longest_flow_path_and_slope(
        self,
        arr: np.ndarray,
        flow_dirs: np.ndarray,
        mask: np.ndarray,
        outlet_r: int,
        outlet_c: int,
        cell_width: float,
        cell_height: float,
        m_per_deg_lat: float,
        m_per_deg_lon: float,
    ) -> Tuple[float, float]:
        """BFS from outlet upstream; track distance along flow. L = max distance (m), slope = (elev_max - elev_outlet) / L."""
        h, w = arr.shape
        dist_cells = np.full((h, w), -1.0)
        dist_cells[outlet_r, outlet_c] = 0
        queue: List[Tuple[int, int]] = [(outlet_r, outlet_c)]
        cell_m = np.sqrt((cell_width * m_per_deg_lon) ** 2 + (cell_height * m_per_deg_lat) ** 2)
        while queue:
            r, c = queue.pop(0)
            d = dist_cells[r, c]
            for dr, dc in _inverse_d8():
                nr, nc = r + dr, c + dc
                if nr < 0 or nr >= h or nc < 0 or nc >= w or not mask[nr, nc]:
                    continue
                ndir = flow_dirs[nr, nc]
                if ndir == 0:
                    continue
                sr, sc = D8_OFFSETS[ndir - 1]
                if nr + sr != r or nc + sc != c:
                    continue
                step = 1.0 if (dr != 0 and dc != 0) else 1.0  # diagonal ~ sqrt2, use 1 for simplicity
                ndist = d + step * cell_m
                if dist_cells[nr, nc] < 0 or ndist > dist_cells[nr, nc]:
                    dist_cells[nr, nc] = ndist
                    queue.append((nr, nc))
        valid = (dist_cells >= 0) & mask
        if not np.any(valid):
            return 0.0, 0.001
        L_m = float(np.max(dist_cells[valid]))
        if L_m <= 0:
            return 0.0, 0.001
        elev_outlet = float(arr[outlet_r, outlet_c])
        elev_max = float(np.nanmax(arr[mask]))
        slope = (elev_max - elev_outlet) / L_m
        slope = max(slope, 0.001)
        return L_m, slope

    def _time_of_concentration_kirpich(self, L_m: float, slope: float) -> float:
        """Kirpich (1940): Tc (min) = 0.0078 * L^0.77 * S^(-0.385), L in m, S = slope (rise/run)."""
        if L_m <= 0 or slope <= 0:
            return 0.0
        return 0.0078 * (L_m ** 0.77) * (slope ** -0.385)

    def _geodesic_area_ha(self, ring: List[List[float]]) -> float:
        """Compute geodesic area (m²) of polygon ring (closed list of [lon, lat]), return hectares."""
        if len(ring) < 3:
            return 0.0
        try:
            poly = ShapelyPolygon(ring)
            if poly.is_empty or not poly.is_valid:
                return 0.0
            geod = Geod(ellps="WGS84")
            area_m2 = abs(geod.geometry_area_perimeter(poly)[0])
            return float(area_m2 / 10000.0)
        except Exception:
            return 0.0

    def _fallback_watershed(self, lat: float, lon: float) -> Watershed:
        """When DEM unavailable, return bbox with geodesic area (non-zero when polygon valid)."""
        minx, miny, maxx, maxy = bbox_from_center(lat, lon, 2000)
        coords = [[minx, miny], [maxx, miny], [maxx, maxy], [minx, maxy], [minx, miny]]
        area_ha = self._geodesic_area_ha(coords)
        return Watershed(
            geometry={"type": "Polygon", "coordinates": [coords]},
            properties={
                "area_ha": round(area_ha, 2),
                "time_of_concentration_min": 0,
                "outlet_lat": lat,
                "outlet_lon": lon,
                "longest_path_m": 0,
                "slope": 0,
            },
        )

    def compute_watershed_grid(
        self, minx: float, miny: float, maxx: float, maxy: float,
        grid_spacing_m: float = 100.0
    ) -> WatershedGrid:
        """
        Compute watershed area and time of concentration for a grid of points within the bbox.
        Returns grid with normalized values for heatmap display.
        """
        import math
        from app.core.geo_utils import meters_per_degree_lat, meters_per_degree_lon
        
        # Calculate center and radius for DEM fetch
        center_lon = (minx + maxx) / 2.0
        center_lat = (miny + maxy) / 2.0
        dlat_deg = maxy - miny
        dlon_deg = maxx - minx
        m_per_deg_lat = meters_per_degree_lat(center_lat)
        m_per_deg_lon = meters_per_degree_lon(center_lat)
        half_width_m = (dlon_deg * m_per_deg_lon) / 2.0
        half_height_m = (dlat_deg * m_per_deg_lat) / 2.0
        radius_m = math.sqrt(half_width_m ** 2 + half_height_m ** 2) * 1.2  # 20% margin
        
        # Fetch DEM once for entire bbox - try Cesium first, fall back to USGS
        dem = self._cesium.fetch_dem(center_lat, center_lon, radius_m)
        terrain_source = "cesium_world_terrain"
        
        if dem is None:
            logger.info("Cesium terrain unavailable, falling back to USGS 3DEP")
            dem = self._usgs.fetch_dem(center_lat, center_lon, radius_m)
            terrain_source = "usgs_3dep"
        
        if dem is None:
            return WatershedGrid(features=[], metadata={"error": "DEM unavailable"})
        
        arr = np.array(dem.get("data", []))
        if arr.size == 0:
            return WatershedGrid(features=[], metadata={"error": "Empty DEM"})
        
        transform = dem.get("transform", [])
        nodata = dem.get("nodata", -9999)
        arr = np.where(arr == nodata, np.nan, arr)
        h, w = arr.shape
        cell_width = abs(transform[0]) if len(transform) >= 1 else 0.0001
        cell_height = abs(transform[4]) if len(transform) >= 5 else 0.0001
        lon_ul, lat_ul = transform[2], transform[5]
        
        # Compute D8 flow direction grid once
        flow_dirs = self._flow_direction_d8(arr)
        
        # Generate grid points based on spacing
        lat_spacing_deg = grid_spacing_m / m_per_deg_lat
        lon_spacing_deg = grid_spacing_m / m_per_deg_lon
        
        # Grid of points
        lats = np.arange(miny, maxy, lat_spacing_deg)
        lons = np.arange(minx, maxx, lon_spacing_deg)
        
        # Storage for results
        results = []
        
        # For normalization
        all_areas = []
        all_tcs = []
        
        # Process each grid point
        for lat in lats:
            for lon in lons:
                # Convert to array indices
                col = int(np.clip((lon - lon_ul) / cell_width, 0, w - 1))
                row = int(np.clip((lat_ul - lat) / cell_height, 0, h - 1))
                
                # Check if within valid DEM area
                if np.isnan(arr[row, col]):
                    continue
                
                # Trace downstream to find pour point
                outlet_r, outlet_c = self._trace_downstream(flow_dirs, row, col, h, w)
                
                # Compute watershed mask
                mask = self._drainage_basin(flow_dirs, outlet_r, outlet_c, h, w)
                if mask is None or np.sum(mask) < 3:
                    continue
                
                # Calculate area
                coords = self._mask_to_polygon(mask, lon_ul, lat_ul, cell_width, cell_height)
                if not coords:
                    continue
                
                area_ha = self._geodesic_area_ha(coords)
                if area_ha <= 0:
                    continue
                
                # Calculate Tc
                L_m, slope = self._longest_flow_path_and_slope(
                    arr, flow_dirs, mask, outlet_r, outlet_c, cell_width, cell_height,
                    m_per_deg_lat, m_per_deg_lon
                )
                tc_min = self._time_of_concentration_kirpich(L_m, slope)
                
                # Store result
                results.append({
                    "lat": float(lat),
                    "lon": float(lon),
                    "area_ha": float(area_ha),
                    "tc_min": float(tc_min),
                })
                all_areas.append(area_ha)
                all_tcs.append(tc_min)
        
        # Normalize values for jet colormap
        if not results:
            return WatershedGrid(features=[], metadata={"error": "No valid grid points"})
        
        min_area = float(np.min(all_areas))
        max_area = float(np.max(all_areas))
        min_tc = float(np.min(all_tcs))
        max_tc = float(np.max(all_tcs))
        
        area_range = max_area - min_area if max_area > min_area else 1.0
        tc_range = max_tc - min_tc if max_tc > min_tc else 1.0
        
        # Create GeoJSON features
        features = []
        for result in results:
            # Compute jet values (0-1 normalized)
            jet_value_area = (result["area_ha"] - min_area) / area_range
            jet_value_tc = (result["tc_min"] - min_tc) / tc_range
            
            # Create a small rectangle around the point for visualization
            half_lat = lat_spacing_deg / 2.0
            half_lon = lon_spacing_deg / 2.0
            rect_coords = [[
                [result["lon"] - half_lon, result["lat"] - half_lat],
                [result["lon"] + half_lon, result["lat"] - half_lat],
                [result["lon"] + half_lon, result["lat"] + half_lat],
                [result["lon"] - half_lon, result["lat"] + half_lat],
                [result["lon"] - half_lon, result["lat"] - half_lat],
            ]]
            
            features.append({
                "type": "Feature",
                "geometry": {
                    "type": "Polygon",
                    "coordinates": rect_coords,
                },
                "properties": {
                    "area_ha": round(result["area_ha"], 2),
                    "tc_min": round(result["tc_min"], 2),
                    "jet_value_area": round(jet_value_area, 4),
                    "jet_value_tc": round(jet_value_tc, 4),
                },
            })
        
        metadata = {
            "grid_spacing_m": grid_spacing_m,
            "point_count": len(features),
            "min_area_ha": round(min_area, 2),
            "max_area_ha": round(max_area, 2),
            "min_tc_min": round(min_tc, 2),
            "max_tc_min": round(max_tc, 2),
            "dem_cell_size_m": round(cell_width * m_per_deg_lon, 2),
            "terrain_source": terrain_source,
        }
        
        return WatershedGrid(features=features, metadata=metadata)

    def get_watershed_contours(
        self, lat: float, lon: float, radius_m: float = 1500, interval_m: float = 5.0
    ) -> WatershedContours:
        """Generate contour lines for the watershed area with jet colormap values."""
        from affine import Affine
        from skimage import measure

        dem = self._usgs.fetch_dem(lat, lon, radius_m)
        if dem is None:
            return WatershedContours(features=[], properties={"error": "DEM unavailable"})

        arr = np.array(dem.get("data", []))
        if arr.size == 0:
            return WatershedContours(features=[], properties={"error": "Empty DEM"})

        transform = dem.get("transform", [])
        nodata = dem.get("nodata", -9999)
        arr = np.where(arr == nodata, np.nan, arr)
        h, w = arr.shape
        cell_width = abs(transform[0]) if len(transform) >= 1 else 0.0001
        cell_height = abs(transform[4]) if len(transform) >= 5 else 0.0001
        lon_ul, lat_ul = transform[2], transform[5]

        # Starting cell (where user clicked)
        col = int(np.clip((lon - lon_ul) / cell_width, 0, w - 1))
        row = int(np.clip((lat_ul - lat) / cell_height, 0, h - 1))

        # Delineate watershed - trace downstream first to find pour point
        flow_dirs = self._flow_direction_d8(arr)
        outlet_r, outlet_c = self._trace_downstream(flow_dirs, row, col, h, w)
        mask = self._drainage_basin(flow_dirs, outlet_r, outlet_c, h, w)
        if mask is None or np.sum(mask) < 3:
            return WatershedContours(features=[], properties={"error": "No watershed found"})

        # Mask the DEM to watershed only
        masked_arr = np.where(mask, arr, np.nan)

        # Get elevation range for normalization
        valid_elevs = masked_arr[~np.isnan(masked_arr)]
        if len(valid_elevs) == 0:
            return WatershedContours(features=[], properties={"error": "No valid elevations"})

        min_elev = float(np.min(valid_elevs))
        max_elev = float(np.max(valid_elevs))
        elev_range = max_elev - min_elev if max_elev > min_elev else 1.0

        # Generate contour levels
        start_level = int(min_elev // interval_m) * interval_m
        end_level = int(max_elev // interval_m + 1) * interval_m
        levels = np.arange(start_level, end_level + interval_m, interval_m)

        aff = Affine(*transform) if isinstance(transform, (list, tuple)) else transform
        features = []

        for level in levels:
            if level < min_elev or level > max_elev:
                continue
            try:
                contours = measure.find_contours(masked_arr, level)
            except Exception:
                continue

            for contour in contours:
                if len(contour) < 3:
                    continue
                coords = []
                for r, c in contour:
                    x, y = aff * (c, r)
                    coords.append([float(x), float(y)])
                if len(coords) < 2:
                    continue

                # Compute jet_value (0-1) for colormap
                jet_value = float((level - min_elev) / elev_range)

                features.append({
                    "type": "Feature",
                    "geometry": {"type": "LineString", "coordinates": coords},
                    "properties": {
                        "elevation": float(level),
                        "jet_value": round(jet_value, 4),
                    },
                })

        # Convert outlet cell back to lat/lon
        outlet_lon = lon_ul + (outlet_c + 0.5) * cell_width
        outlet_lat = lat_ul - (outlet_r + 0.5) * cell_height

        return WatershedContours(
            features=features,
            properties={
                "min_elevation": round(min_elev, 2),
                "max_elevation": round(max_elev, 2),
                "interval_m": interval_m,
                "contour_count": len(features),
                "outlet_lat": outlet_lat,
                "outlet_lon": outlet_lon,
            },
        )
