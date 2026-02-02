from fastapi import APIRouter, Depends
from app.schemas.analysis_schemas import FloodZoneResponse
from app.models.flood_risk import FloodRiskModel
from app.core.deps import get_flood_risk_model

router = APIRouter(prefix="/api/flood", tags=["flood"])


@router.get("/zones", response_model=FloodZoneResponse)
def get_flood_zones(
    minx: float,
    miny: float,
    maxx: float,
    maxy: float,
    model: FloodRiskModel = Depends(get_flood_risk_model),
):
    zones = model.get_flood_zones(minx, miny, maxx, maxy)
    return FloodZoneResponse.from_domain(zones)


@router.get("/point")
def get_flood_zone_at_point(
    lat: float,
    lon: float,
    model: FloodRiskModel = Depends(get_flood_risk_model),
):
    zone = model.get_zone_at_point(lat, lon)
    if zone is None:
        return {"zone": None, "description": "Not in mapped flood zone"}
    return {"zone": zone.zone_code, "description": zone.description}
