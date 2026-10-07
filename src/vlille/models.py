"""Pydantic models of the GBFS feeds used by the project.

Only the fields we use are declared; unknown fields are ignored, so a new field on the producer
side does not break the collection. Epoch timestamps are converted to UTC datetimes.
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
    """Header shared by all GBFS feeds."""

    last_updated: datetime
    ttl: int = Field(ge=0)
    version: str


class StationInformationFeed(GbfsFeed):
    data: StationInformationData


class StationStatusFeed(GbfsFeed):
    data: StationStatusData
