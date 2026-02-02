from pydantic_settings import BaseSettings
from pydantic import ConfigDict


class Settings(BaseSettings):
    model_config = ConfigDict(env_file=".env", env_file_encoding="utf-8")

    usgs_base_url: str = "https://elevation.nationalmap.gov/arcgis/rest/services"
    nhd_base_url: str = "https://hydro.nationalmap.gov/arcgis/rest/services"
    fema_base_url: str = "https://hazards.fema.gov/gis/nfhl/rest/services/public"
    osm_base_url: str = "https://api.openstreetmap.org"


settings = Settings()
