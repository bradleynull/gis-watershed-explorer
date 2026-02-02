def test_elevation_model_get_contours(elevation_model):
    contours = elevation_model.get_contours(35.2, -80.6, 500, 2)
    assert contours.type == "FeatureCollection"
    assert isinstance(contours.features, list)
