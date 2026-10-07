import gzip
from datetime import date

from fakes import FakeBucket, FakeConsumer, FakeMessage

from vlille.consume import flush, object_name, write_batch

# 2026-10-07T11:08:03Z en millisecondes
TIMESTAMP_MS = 1791371283000


def message(partition: int, offset: int, station_id: str) -> FakeMessage:
    value = f'{{"station_id": "{station_id}"}}'.encode()
    return FakeMessage(partition, offset, value, TIMESTAMP_MS)


def test_object_name_contains_day_partition_and_first_offset():
    assert (
        object_name(1, 146, date(2026, 10, 7))
        == "kafka/station_status/dt=2026-10-07/p1-000000000146.ndjson.gz"
    )


def test_one_file_per_partition_with_one_line_per_message():
    bucket = FakeBucket()
    batch = [message(0, 10, "8"), message(2, 5, "13"), message(0, 11, "21")]

    names = write_batch(bucket, batch)

    assert names == [
        "kafka/station_status/dt=2026-10-07/p0-000000000010.ndjson.gz",
        "kafka/station_status/dt=2026-10-07/p2-000000000005.ndjson.gz",
    ]
    lines = gzip.decompress(bucket.objects[names[0]]).splitlines()
    assert lines == [b'{"station_id": "8"}', b'{"station_id": "21"}']


def test_offsets_are_committed_after_the_files_are_written():
    bucket = FakeBucket()
    consumer = FakeConsumer(bucket)

    flush(consumer, bucket, [message(0, 10, "8")])

    assert consumer.objects_at_commit == [
        "kafka/station_status/dt=2026-10-07/p0-000000000010.ndjson.gz"
    ]
