import json
from datetime import date

import pytest
from fakes import FakeBigQuery, FakeBucket
from google.cloud import bigquery

from vlille.load import load_day, read_day
from vlille.raw_store import RawStore

DAY = date(2026, 10, 6)


@pytest.fixture
def bucket(load_fixture) -> FakeBucket:
    """Zone brute contenant un fichier de chaque flux pour le 2026-10-06."""
    bucket = FakeBucket()
    store = RawStore(bucket)
    for feed in ("station_information", "station_status"):
        store.write(feed, json.dumps(load_fixture(feed)).encode())
    return bucket


def test_each_file_becomes_one_row(bucket, load_fixture):
    rows = read_day(bucket, "station_status", DAY)

    assert len(rows) == 1
    assert rows[0]["last_updated"] == "2026-10-06T15:12:02+00:00"
    assert rows[0]["source_uri"].startswith(
        "gs://bucket-de-test/gbfs/station_status/dt=2026-10-06/"
    )
    assert rows[0]["payload"] == load_fixture("station_status")


def test_other_days_are_not_read(bucket):
    assert read_day(bucket, "station_status", date(2026, 10, 7)) == []


def test_day_partition_is_replaced(bucket):
    bq = FakeBigQuery()

    loaded = load_day(bq, bucket, "projet.vlille_raw", DAY)

    assert loaded == {"station_information": 1, "station_status": 1}
    tables = [table for table, _, _ in bq.loads]
    assert tables == [
        "projet.vlille_raw.raw_station_information$20261006",
        "projet.vlille_raw.raw_station_status$20261006",
    ]
    job_config = bq.loads[0][2]
    assert job_config.write_disposition == bigquery.WriteDisposition.WRITE_TRUNCATE


def test_empty_day_loads_nothing():
    bq = FakeBigQuery()

    loaded = load_day(bq, FakeBucket(), "projet.vlille_raw", DAY)

    assert loaded == {"station_information": 0, "station_status": 0}
    assert bq.loads == []
