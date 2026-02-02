from typing import List, Any, Dict
from pydantic import BaseModel
from app.models.drainage import FlowPath
from app.models.watershed import Rivers, Watershed, WatershedContours


class RiversResponse(BaseModel):
    type: str = "FeatureCollection"
    features: List[Any] = []

    @classmethod
    def from_domain(cls, rivers: Rivers) -> "RiversResponse":
        return cls(type=rivers.type, features=rivers.features)


class FlowPathResponse(BaseModel):
    type: str = "Feature"
    geometry: dict
    properties: dict

    @classmethod
    def from_domain(cls, flow_path: FlowPath) -> "FlowPathResponse":
        return cls(
            type="Feature",
            geometry=flow_path.geometry,
            properties=flow_path.properties,
        )


class WatershedResponse(BaseModel):
    type: str = "Feature"
    geometry: dict
    properties: dict

    @classmethod
    def from_domain(cls, watershed: Watershed) -> "WatershedResponse":
        return cls(
            type="Feature",
            geometry=watershed.geometry,
            properties=watershed.properties,
        )


class WatershedContoursResponse(BaseModel):
    type: str = "FeatureCollection"
    features: List[Any] = []
    properties: dict = {}

    @classmethod
    def from_domain(cls, contours: WatershedContours) -> "WatershedContoursResponse":
        return cls(
            type=contours.type,
            features=contours.features,
            properties=contours.properties or {},
        )


class WatershedGridResponse(BaseModel):
    type: str = "FeatureCollection"
    features: List[Dict[str, Any]] = []
    metadata: Dict[str, Any] = {}

    @classmethod
    def from_features(cls, features: List[Dict[str, Any]], metadata: Dict[str, Any]) -> "WatershedGridResponse":
        return cls(
            type="FeatureCollection",
            features=features,
            metadata=metadata,
        )
