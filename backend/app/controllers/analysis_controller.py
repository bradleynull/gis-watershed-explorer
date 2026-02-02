from fastapi import APIRouter, Depends
from app.schemas.analysis_schemas import PlacementSuggestionsResponse, BuildabilityResponse
from app.models.placement import PlacementModel
from app.core.deps import get_placement_model

router = APIRouter(prefix="/api/analysis", tags=["analysis"])


@router.post("/optimal-placement", response_model=PlacementSuggestionsResponse)
def get_optimal_placement(
    lat: float,
    lon: float,
    radius_m: float = 500,
    num_suggestions: int = 5,
    model: PlacementModel = Depends(get_placement_model),
):
    suggestions = model.suggest_placements(lat, lon, radius_m, num_suggestions)
    return PlacementSuggestionsResponse.from_domain(suggestions)


@router.get("/buildability", response_model=BuildabilityResponse)
def get_buildability(
    lat: float,
    lon: float,
    model: PlacementModel = Depends(get_placement_model),
):
    result = model.can_build_at(lat, lon)
    return BuildabilityResponse.from_domain(result)
