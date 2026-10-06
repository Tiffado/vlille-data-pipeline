import gzip
import json
from datetime import UTC, datetime

import pytest
from fakes import FakeBucket

from vlille.raw_store import RawStore, RawStoreError, object_name, read_last_updated


@pytest.fixture
def payload(load_fixture) -> bytes:
    return json.dumps(load_fixture("station_status")).encode()


def test_object_name_is_hive_partitioned_by_day():
    ts = datetime(2026, 10, 6, 15, 12, 2, tzinfo=UTC)

    assert (
        object_name("station_status", ts)
        == "gbfs/station_status/dt=2026-10-06/station_status_20261006T151202Z.json.gz"
    )


def test_last_updated_is_read_from_payload(payload):
    assert read_last_updated(payload) == datetime(2026, 10, 6, 15, 12, 2, tzinfo=UTC)


@pytest.mark.parametrize("bad", [b"pas du json", b"{}", b'{"last_updated": "demain"}'])
def test_unreadable_last_updated_raises(bad):
    with pytest.raises(RawStoreError):
        read_last_updated(bad)


def test_payload_is_stored_gzipped_and_unchanged(payload):
    bucket = FakeBucket()

    name, written = RawStore(bucket).write("station_status", payload)

    assert written is True
    assert gzip.decompress(bucket.objects[name]) == payload
    assert bucket.content_types[name] == "application/gzip"


def test_same_state_written_twice_is_stored_once(payload):
    bucket = FakeBucket()
    store = RawStore(bucket)

    first = store.write("station_status", payload)
    second = store.write("station_status", payload)

    assert first == (second[0], True)
    assert second[1] is False
    assert len(bucket.objects) == 1


def test_compression_is_deterministic(payload):
    bucket = FakeBucket()

    name, _ = RawStore(bucket).write("station_status", payload)

    # Octets 4 à 7 de l'en-tête gzip : date de compression, fixée à 0.
    assert bucket.objects[name][4:8] == bytes(4)
