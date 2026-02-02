"""Convert Overpass API response to GeoJSON."""


def overpass_to_geojson(data: dict) -> dict:
    """Convert Overpass JSON to GeoJSON FeatureCollection."""
    features = []
    elements = data.get("elements", [])
    nodes = {e["id"]: (e.get("lon"), e.get("lat")) for e in elements if e.get("type") == "node"}
    for e in elements:
        if e.get("type") != "way":
            continue
        coords = []
        for nid in e.get("nodes", []):
            if nid in nodes:
                lon, lat = nodes[nid]
                coords.append([lon, lat])
        if len(coords) < 2:
            continue
        if coords[0] != coords[-1]:
            coords.append(coords[0])
        features.append({
            "type": "Feature",
            "geometry": {"type": "Polygon", "coordinates": [coords]},
            "properties": e.get("tags", {}),
        })
    return {"type": "FeatureCollection", "features": features}
