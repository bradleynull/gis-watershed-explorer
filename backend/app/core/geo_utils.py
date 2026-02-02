import math
from typing import Tuple


def latlon_to_web_mercator(lat: float, lon: float) -> Tuple[float, float]:
    """Convert WGS84 lat/lon to Web Mercator (EPSG:3857) x, y in meters."""
    x = lon * 20037508.34 / 180
    y = math.log(math.tan((90 + lat) * math.pi / 360)) / (math.pi / 180) * 20037508.34 / 180
    return x, y


def web_mercator_to_latlon(x: float, y: float) -> Tuple[float, float]:
    """Convert Web Mercator x, y to WGS84 lat/lon."""
    lon = x * 180 / 20037508.34
    lat = 360 / math.pi * (math.atan(math.exp(y * math.pi / 20037508.34)) - math.pi / 4) - 90
    return lat, lon


def meters_per_degree_lat(lat: float) -> float:
    """Approximate meters per degree latitude at given latitude."""
    return 111320  # ~constant


def meters_per_degree_lon(lat: float) -> float:
    """Approximate meters per degree longitude at given latitude."""
    return 111320 * math.cos(math.radians(lat))


def bbox_from_center(lat: float, lon: float, radius_m: float) -> Tuple[float, float, float, float]:
    """Return (minx, miny, maxx, maxy) in WGS84 for a square bbox around center."""
    dlat = radius_m / meters_per_degree_lat(lat)
    dlon = radius_m / meters_per_degree_lon(lat)
    return lon - dlon, lat - dlat, lon + dlon, lat + dlat
