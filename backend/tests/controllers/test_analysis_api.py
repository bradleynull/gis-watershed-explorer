def test_buildability(client):
    r = client.get("/api/analysis/buildability?lat=35.2&lon=-80.6")
    assert r.status_code == 200
    data = r.json()
    assert "can_build" in data
    assert "reasons" in data


def test_optimal_placement(client):
    r = client.post("/api/analysis/optimal-placement?lat=35.2&lon=-80.6&radius_m=500&num_suggestions=3")
    assert r.status_code == 200
    data = r.json()
    assert "suggestions" in data
    assert isinstance(data["suggestions"], list)
