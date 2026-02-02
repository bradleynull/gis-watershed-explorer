from functools import lru_cache
from app.models.elevation import ElevationModel
from app.models.drainage import DrainageModel
from app.models.watershed import WatershedModel
from app.models.flood_risk import FloodRiskModel
from app.models.placement import PlacementModel


@lru_cache()
def get_elevation_model() -> ElevationModel:
    return ElevationModel()


def get_drainage_model() -> DrainageModel:
    return DrainageModel()


def get_watershed_model() -> WatershedModel:
    return WatershedModel()


def get_flood_risk_model() -> FloodRiskModel:
    return FloodRiskModel()


def get_placement_model() -> PlacementModel:
    return PlacementModel()
