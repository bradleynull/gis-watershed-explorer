from fastapi import APIRouter, Depends, Query
from app.schemas.hydrology_schemas import WatershedGridResponse
from app.models.watershed import WatershedModel
from app.core.deps import get_watershed_model

router = APIRouter(prefix="/api/hydrology", tags=["hydrology"])


@router.get("/watershed/grid", response_model=WatershedGridResponse)
def get_watershed_grid(
    minx: float,
    miny: float,
    maxx: float,
    maxy: float,
    grid_spacing_m: float = Query(100.0, ge=50, le=1000),
    model: WatershedModel = Depends(get_watershed_model),
):
    """
    Compute watershed area and time of concentration for a grid of points within the bbox.
    Returns GeoJSON FeatureCollection with normalized values for heatmap display.
    """
    grid = model.compute_watershed_grid(minx, miny, maxx, maxy, grid_spacing_m)
    return WatershedGridResponse.from_features(grid.features, grid.metadata)
