def test_flood_zones(client):
    r = client.get("/api/flood/zones?minx=-80.7&miny=35.1&maxx=-80.5&maxy=35.3")
    assert r.status_code == 200
    data = r.json()
    assert data["type"] == "FeatureCollection"
    assert "features" in data


def test_flood_point(client):
    r = client.get("/api/flood/point?lat=35.2&lon=-80.6")
    assert r.status_code == 200
    data = r.json()
    assert "zone" in data
    assert "description" in data
