import gzip
import json
from datetime import date

import pytest
from fakes import FakeBigQuery, FakeBucket
from google.cloud import bigquery

from vlille.load import load_day, read_station_events, read_station_information
from vlille.raw_store import RawStore

DAY = date(2026, 10, 6)
EVENTS_FILE = "kafka/station_status/dt=2026-10-06/p0-000000000010.ndjson.gz"


@pytest.fixture
def bucket(load_fixture) -> FakeBucket:
    """Zone brute du 2026-10-06 : un fichier du référentiel et un fichier de 2 messages Kafka."""
    bucket = FakeBucket()
    RawStore(bucket).write(
        "station_information", json.dumps(load_fixture("station_information")).encode()
    )
    lines = b'{"station_id": "2"}\n{"station_id": "3"}\n'
    bucket.blob(EVENTS_FILE).upload_from_string(gzip.compress(lines), "application/gzip")
    return bucket


def test_each_information_file_becomes_one_row(bucket, load_fixture):
    rows = read_station_information(bucket, DAY)

    assert len(rows) == 1
    assert rows[0]["last_updated"] == "2026-10-06T15:12:04+00:00"
    assert rows[0]["payload"] == load_fixture("station_information")


def test_each_kafka_message_becomes_one_row(bucket):
    rows = read_station_events(bucket, DAY)

    assert [row["payload"] for row in rows] == [{"station_id": "2"}, {"station_id": "3"}]
    assert rows[0]["ingestion_date"] == "2026-10-06"
    assert rows[0]["source_uri"] == "gs://bucket-de-test/" + EVENTS_FILE


def test_other_days_are_not_read(bucket):
    assert read_station_information(bucket, date(2026, 10, 7)) == []
    assert read_station_events(bucket, date(2026, 10, 7)) == []


def test_day_partitions_are_replaced(bucket):
    bq = FakeBigQuery()

    loaded = load_day(bq, bucket, "projet.vlille_raw", DAY)

    assert loaded == {"raw_station_information": 1, "raw_station_status_stream": 2}
    tables = [table for table, _, _ in bq.loads]
    assert tables == [
        "projet.vlille_raw.raw_station_information$20261006",
        "projet.vlille_raw.raw_station_status_stream$20261006",
    ]
    job_config = bq.loads[0][2]
    assert job_config.write_disposition == bigquery.WriteDisposition.WRITE_TRUNCATE


def test_empty_day_loads_nothing():
    bq = FakeBigQuery()

    loaded = load_day(bq, FakeBucket(), "projet.vlille_raw", DAY)

    assert loaded == {"raw_station_information": 0, "raw_station_status_stream": 0}
    assert bq.loads == []
