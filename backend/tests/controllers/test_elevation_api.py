def test_get_contours(client, elevation_model):
    from app.core.deps import get_elevation_model
    from app.main import app
    app.dependency_overrides[get_elevation_model] = lambda: elevation_model

    r = client.get("/api/elevation/contours?lat=35.2&lon=-80.6&radius_m=500&interval_m=2")
    assert r.status_code == 200
    data = r.json()
    assert data["type"] == "FeatureCollection"
    assert "features" in data

    app.dependency_overrides.clear()


def test_contours_for_bbox(client, elevation_model):
    """Test bbox contour endpoint returns valid GeoJSON with jet_value."""
    from app.core.deps import get_elevation_model
    from app.main import app

    app.dependency_overrides[get_elevation_model] = lambda: elevation_model

    # bbox: minx, miny, maxx, maxy (lon, lat)
    r = client.get(
        "/api/elevation/contours/bbox?minx=-80.61&miny=35.29&maxx=-80.59&maxy=35.31&interval_m=5"
    )
    assert r.status_code == 200
    data = r.json()
    assert data["type"] == "FeatureCollection"
    assert "features" in data

    features = data["features"]
    # With mock 10x10 DEM we may get zero or more contours
    for feature in features:
        assert feature["type"] == "Feature"
        assert feature["geometry"]["type"] == "LineString"
        props = feature["properties"]
        assert "elevation" in props
        assert "jet_value" in props
        assert 0 <= props["jet_value"] <= 1, "jet_value should be normalized 0-1"

    app.dependency_overrides.clear()
