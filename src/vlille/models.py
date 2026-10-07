"""Modèles des flux GBFS utilisés par le projet.

Seuls les champs exploités sont déclarés ; les champs inconnus sont ignorés, pour qu'un ajout
côté producteur ne casse pas la collecte. Les horodatages GBFS (secondes epoch) sont convertis en
datetime UTC.
"""

from datetime import datetime

from pydantic import BaseModel, Field


class StationInformation(BaseModel):
    station_id: str
    name: str
    capacity: int = Field(ge=0)
    lat: float = Field(ge=-90, le=90)
    lon: float = Field(ge=-180, le=180)
    post_code: str | None = None
    is_virtual_station: bool = False


class StationStatus(BaseModel):
    station_id: str
    num_bikes_available: int = Field(ge=0)
    num_docks_available: int = Field(ge=0)
    is_installed: bool
    is_renting: bool
    is_returning: bool
    last_reported: datetime


class StationInformationData(BaseModel):
    stations: list[StationInformation]


class StationStatusData(BaseModel):
    stations: list[StationStatus]


class GbfsFeed(BaseModel):
    """En-tête commun à tous les flux GBFS."""

    last_updated: datetime
    ttl: int = Field(ge=0)
    version: str


class StationInformationFeed(GbfsFeed):
    data: StationInformationData


class StationStatusFeed(GbfsFeed):
    data: StationStatusData
