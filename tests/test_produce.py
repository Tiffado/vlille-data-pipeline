import json
from datetime import UTC, datetime

import pytest
from fakes import FakeProducer

from vlille.models import StationStatusFeed
from vlille.produce import TOPIC, new_reports, publish, to_message


@pytest.fixture
def feed(load_fixture) -> StationStatusFeed:
    return StationStatusFeed.model_validate(load_fixture("station_status"))


def test_first_poll_reports_every_station(feed):
    last_seen = {}

    changed = new_reports(feed, last_seen)

    assert [s.station_id for s in changed] == ["2", "3"]
    assert set(last_seen) == {"2", "3"}


def test_unchanged_station_is_not_reported_again(feed):
    last_seen = {}
    new_reports(feed, last_seen)

    assert new_reports(feed, last_seen) == []


def test_station_with_new_report_is_reported(feed, load_fixture):
    last_seen = {}
    new_reports(feed, last_seen)
    raw = load_fixture("station_status")
    raw["data"]["stations"][0]["last_reported"] += 60
    later = StationStatusFeed.model_validate(raw)

    assert [s.station_id for s in new_reports(later, last_seen)] == ["2"]


def test_message_contains_station_state_and_feed_time(feed):
    station = feed.data.stations[0]

    message = json.loads(to_message(station, feed.last_updated))

    assert message["station_id"] == "2"
    assert message["num_docks_available"] == 31
    assert message["last_reported"] == station.last_reported.isoformat().replace("+00:00", "Z")
    assert message["feed_updated_at"] == "2026-10-06T15:12:02+00:00"


def test_each_station_is_published_with_its_id_as_key(feed):
    producer = FakeProducer()

    publish(producer, feed.data.stations, datetime(2026, 10, 6, tzinfo=UTC))

    assert [(topic, key) for topic, key, _ in producer.messages] == [(TOPIC, "2"), (TOPIC, "3")]
    assert producer.flushed
