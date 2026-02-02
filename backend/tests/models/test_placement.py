from app.models.placement import PlacementModel, PlacementSuggestion, BuildabilityResult


def test_placement_suggestion_to_dict():
    s = PlacementSuggestion(lat=35.2, lon=-80.6, score=0.8, reason="test")
    d = s.to_dict()
    assert d["lat"] == 35.2
    assert d["lon"] == -80.6
    assert d["score"] == 0.8
    assert d["reason"] == "test"


def test_placement_model_suggest_placements():
    model = PlacementModel()
    suggestions = model.suggest_placements(35.2, -80.6, 500, 3)
    assert isinstance(suggestions, list)
    assert len(suggestions) <= 3
    for s in suggestions:
        assert isinstance(s, PlacementSuggestion)


def test_placement_model_can_build_at():
    model = PlacementModel()
    result = model.can_build_at(35.2, -80.6)
    assert isinstance(result, BuildabilityResult)
    assert isinstance(result.can_build, bool)
    assert isinstance(result.reasons, list)
