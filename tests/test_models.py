from datetime import UTC, datetime

import pytest
from pydantic import ValidationError

from vlille.models import StationInformationFeed, StationStatus, StationStatusFeed


def test_station_information_feed_is_parsed(load_fixture):
    feed = StationInformationFeed.model_validate(load_fixture("station_information"))

    assert feed.version == "2.3"
    assert [s.station_id for s in feed.data.stations] == ["1", "2", "3"]
    assert feed.data.stations[0].capacity == 36


def test_station_status_feed_is_parsed(load_fixture):
    feed = StationStatusFeed.model_validate(load_fixture("station_status"))

    assert [s.station_id for s in feed.data.stations] == ["2", "3"]
    assert feed.data.stations[0].num_docks_available == 31


def test_epoch_timestamps_become_utc_datetimes(load_fixture):
    feed = StationStatusFeed.model_validate(load_fixture("station_status"))

    assert feed.last_updated == datetime(2026, 10, 6, 15, 12, 2, tzinfo=UTC)
    assert feed.data.stations[0].last_reported.tzinfo == UTC


def test_unknown_fields_are_ignored(load_fixture):
    raw = load_fixture("station_status")
    raw["data"]["stations"][0]["nouveau_champ"] = "ajouté par le producteur"

    StationStatusFeed.model_validate(raw)


def test_negative_bike_count_is_rejected():
    with pytest.raises(ValidationError):
        StationStatus(
            station_id="2",
            num_bikes_available=-1,
            num_docks_available=31,
            is_installed=True,
            is_renting=True,
            is_returning=True,
            last_reported=1791299410,
        )


def test_missing_required_field_is_rejected(load_fixture):
    raw = load_fixture("station_status")
    del raw["data"]["stations"][0]["is_renting"]

    with pytest.raises(ValidationError):
        StationStatusFeed.model_validate(raw)
