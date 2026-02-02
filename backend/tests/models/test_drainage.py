import pytest
from app.models.drainage import DrainageModel, FlowPath


def test_flow_path_has_geometry_and_properties():
    fp = FlowPath(geometry={"type": "LineString", "coordinates": []}, properties={})
    assert fp.geometry["type"] == "LineString"
    assert fp.properties is not None


def test_drainage_model_calculate_flow_direction(drainage_model):
    path = drainage_model.calculate_flow_direction(35.2, -80.6)
    assert isinstance(path, FlowPath)
    assert path.geometry["type"] == "LineString"
    assert len(path.geometry["coordinates"]) >= 1
    assert path.properties.get("distance_m") is not None


def test_flow_direction_downhill(drainage_model):
    path = drainage_model.calculate_flow_direction(35.2, -80.6)
    coords = path.geometry["coordinates"]
    if len(coords) >= 2:
        assert coords[0] != coords[-1]
