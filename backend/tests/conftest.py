import json
import pytest
import numpy as np
from pathlib import Path
from fastapi.testclient import TestClient

from app.main import app
from app.models.elevation import ElevationModel
from app.models.drainage import DrainageModel
from app.models.watershed import WatershedModel
from app.models.flood_risk import FloodRiskModel
from app.models.placement import PlacementModel
from app.data.usgs_client import USGSClient

FIXTURES_DIR = Path(__file__).parent / "fixtures"


@pytest.fixture
def client():
    return TestClient(app)


@pytest.fixture
def sample_dem():
    """Synthetic 10x10 DEM for testing."""
    size = 10
    arr = np.zeros((size, size))
    for i in range(size):
        for j in range(size):
            arr[i, j] = 100 - (i + j) * 2 + np.random.rand() * 0.5
    return {
        "data": arr.tolist(),
        "transform": [0.0001, 0, -80.6, 0, -0.0001, 35.3],
        "nodata": -9999,
    }


@pytest.fixture
def elevation_model(sample_dem):
    class MockUSGS:
        def fetch_dem(self, lat, lon, radius_m):
            return sample_dem
    return ElevationModel(usgs_client=MockUSGS())


@pytest.fixture
def drainage_model(sample_dem):
    class MockUSGS:
        def fetch_dem(self, lat, lon, radius_m):
            return sample_dem
    return DrainageModel(usgs_client=MockUSGS())


@pytest.fixture
def watershed_fixture_dem():
    """Load fixture DEM that produces a non-trivial watershed (bowl, outlet at center)."""
    path = FIXTURES_DIR / "watershed_fixture_dem.json"
    with open(path) as f:
        return json.load(f)


@pytest.fixture
def expected_watershed():
    """Expected area_ha and time_of_concentration_min for fixture DEM."""
    path = FIXTURES_DIR / "expected_watershed.json"
    with open(path) as f:
        return json.load(f)


@pytest.fixture
def watershed_model(watershed_fixture_dem):
    """WatershedModel that returns fixture DEM for any lat/lon/radius."""
    class MockUSGS:
        def fetch_dem(self, lat, lon, radius_m):
            return watershed_fixture_dem
    return WatershedModel(usgs_client=MockUSGS())
