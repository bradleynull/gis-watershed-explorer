from fastapi import APIRouter, Depends, HTTPException
from app.schemas.elevation_schemas import ContourResponse
from app.models.elevation import ElevationModel
from app.core.deps import get_elevation_model

router = APIRouter(prefix="/api/elevation", tags=["elevation"])


@router.get("/contours", response_model=ContourResponse)
def get_contours(
    lat: float,
    lon: float,
    radius_m: float = 500,
    interval_m: float = 2,
    model: ElevationModel = Depends(get_elevation_model),
):
    contours = model.get_contours(lat, lon, radius_m, interval_m)
    return ContourResponse.from_domain(contours)


@router.get("/contours/bbox", response_model=ContourResponse)
def get_contours_for_bbox(
    minx: float,
    miny: float,
    maxx: float,
    maxy: float,
    interval_m: float = 5.0,
    model: ElevationModel = Depends(get_elevation_model),
):
    """Generate contours for a bounding box region with jet colormap values."""
    contours = model.get_contours_for_bbox(minx, miny, maxx, maxy, interval_m)
    return ContourResponse.from_domain(contours)
