def test_flow_direction(client, drainage_model):
    from app.core.deps import get_drainage_model
    from app.main import app
    app.dependency_overrides[get_drainage_model] = lambda: drainage_model

    r = client.get("/api/hydrology/flow-direction?lat=35.2&lon=-80.6")
    assert r.status_code == 200
    data = r.json()
    assert data["type"] == "Feature"
    assert "geometry" in data
    assert data["geometry"]["type"] == "LineString"
    assert "coordinates" in data["geometry"]
    assert "distance_m" in data.get("properties", {})

    app.dependency_overrides.clear()


def test_rivers(client):
    r = client.get("/api/hydrology/rivers?minx=-80.7&miny=35.1&maxx=-80.5&maxy=35.3")
    assert r.status_code == 200
    data = r.json()
    assert data["type"] == "FeatureCollection"
    assert "features" in data


def test_watershed(client):
    r = client.get("/api/hydrology/watershed?lat=35.2&lon=-80.6")
    assert r.status_code == 200
    data = r.json()
    assert data["type"] == "Feature"
    assert "geometry" in data
    assert data["geometry"]["type"] == "Polygon"
    assert "coordinates" in data["geometry"]
    props = data.get("properties", {})
    assert "area_ha" in props
    assert "time_of_concentration_min" in props


def test_watershed_fixture_values(client, watershed_model, expected_watershed):
    """Fixture-based test: watershed endpoint returns non-zero area_ha and Tc matching expected."""
    from app.core.deps import get_watershed_model
    from app.main import app

    app.dependency_overrides[get_watershed_model] = lambda: watershed_model

    # Fixture DEM is 20x20 with outlet at center; use same lat/lon/radius as fixture transform
    r = client.get(
        "/api/hydrology/watershed?lat=35.2&lon=-80.6&radius_m=500"
    )
    assert r.status_code == 200
    data = r.json()
    props = data.get("properties", {})
    area_ha = props["area_ha"]
    tc_min = props["time_of_concentration_min"]

    assert area_ha > 0, "area_ha should be positive with fixture DEM"
    assert tc_min > 0, "time_of_concentration_min should be positive with fixture DEM"

    tol_area = expected_watershed["tolerance_area_pct"] / 100.0
    tol_tc = expected_watershed["tolerance_tc_pct"] / 100.0
    assert abs(area_ha - expected_watershed["area_ha"]) <= expected_watershed["area_ha"] * tol_area, (
        f"area_ha {area_ha} outside tolerance of expected {expected_watershed['area_ha']}"
    )
    assert abs(tc_min - expected_watershed["time_of_concentration_min"]) <= (
        expected_watershed["time_of_concentration_min"] * tol_tc
    ), (
        f"time_of_concentration_min {tc_min} outside tolerance of expected {expected_watershed['time_of_concentration_min']}"
    )

    app.dependency_overrides.clear()


def test_watershed_contours(client, watershed_model):
    """Test watershed contour endpoint returns valid GeoJSON with jet_value."""
    from app.core.deps import get_watershed_model
    from app.main import app

    app.dependency_overrides[get_watershed_model] = lambda: watershed_model

    r = client.get(
        "/api/hydrology/watershed/contours?lat=35.2&lon=-80.6&radius_m=500&interval_m=10"
    )
    assert r.status_code == 200
    data = r.json()
    assert data["type"] == "FeatureCollection"
    assert "features" in data
    assert "properties" in data

    # Should have contours
    features = data["features"]
    assert len(features) > 0, "Should have at least one contour"

    # Each feature should have elevation and jet_value
    for feature in features:
        assert feature["type"] == "Feature"
        assert feature["geometry"]["type"] == "LineString"
        props = feature["properties"]
        assert "elevation" in props
        assert "jet_value" in props
        assert 0 <= props["jet_value"] <= 1, "jet_value should be normalized 0-1"

    # Properties should include metadata
    props = data["properties"]
    assert "min_elevation" in props
    assert "max_elevation" in props
    assert "contour_count" in props
    assert props["contour_count"] == len(features)

    app.dependency_overrides.clear()


def test_watershed_grid_returns_valid_features(client, watershed_model):
    """Test watershed grid endpoint returns valid GeoJSON features with area_ha, tc_min, and jet values."""
    from app.core.deps import get_watershed_model
    from app.main import app

    app.dependency_overrides[get_watershed_model] = lambda: watershed_model

    # Small bbox for faster computation
    r = client.get(
        "/api/hydrology/watershed/grid?minx=-80.65&miny=35.15&maxx=-80.55&maxy=35.25&grid_spacing_m=200"
    )
    assert r.status_code == 200
    data = r.json()
    
    assert data["type"] == "FeatureCollection"
    assert "features" in data
    assert "metadata" in data
    
    features = data["features"]
    assert len(features) > 0, "Should have at least one grid point"
    
    # Each feature should have required properties
    for feature in features:
        assert feature["type"] == "Feature"
        assert feature["geometry"]["type"] == "Polygon"
        props = feature["properties"]
        assert "area_ha" in props
        assert "tc_min" in props
        assert "jet_value_area" in props
        assert "jet_value_tc" in props
        
        # Validate values
        assert props["area_ha"] > 0, "area_ha should be positive"
        assert props["tc_min"] > 0, "tc_min should be positive"
        assert 0 <= props["jet_value_area"] <= 1, "jet_value_area should be 0-1"
        assert 0 <= props["jet_value_tc"] <= 1, "jet_value_tc should be 0-1"
    
    # Metadata should have min/max values
    metadata = data["metadata"]
    assert "min_area_ha" in metadata
    assert "max_area_ha" in metadata
    assert "min_tc_min" in metadata
    assert "max_tc_min" in metadata
    assert "point_count" in metadata
    assert metadata["point_count"] == len(features)
    
    app.dependency_overrides.clear()
