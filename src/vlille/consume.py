"""`vlille-consume`: writes Kafka messages to the GCS raw zone, in batches.

Offsets are committed only after the batch is written to GCS. If the consumer stops in between,
the batch is read again on restart: at-least-once delivery, duplicates removed later in dbt.
"""

import argparse
import gzip
import logging
import sys
import time
from collections import defaultdict
from datetime import UTC, date, datetime

from confluent_kafka import Consumer, Message
from google.cloud import storage

from vlille.paths import KAFKA_PREFIX
from vlille.produce import TOPIC
from vlille.settings import env

GROUP_ID = "vlille-gcs-writer"

log = logging.getLogger("vlille.consume")


def object_name(partition: int, first_offset: int, day: date) -> str:
    """e.g. kafka/station_status/dt=2026-10-07/p1-000000000146.ndjson.gz"""
    # Zero-padded offset, so the files of a partition sort in order.
    return f"{KAFKA_PREFIX}/dt={day.isoformat()}/p{partition}-{first_offset:012d}.ndjson.gz"


def write_batch(bucket: storage.Bucket, messages: list[Message], day: date) -> list[str]:
    """Write one file per partition (one JSON line per message) and return the file names."""
    by_partition: dict[int, list[Message]] = defaultdict(list)
    for message in messages:
        by_partition[message.partition()].append(message)

    names = []
    for partition, partition_messages in sorted(by_partition.items()):
        first_offset = partition_messages[0].offset()
        name = object_name(partition, first_offset, day)
        lines = b"\n".join(message.value() for message in partition_messages) + b"\n"
        bucket.blob(name).upload_from_string(gzip.compress(lines), content_type="application/gzip")
        names.append(name)
    return names


def flush(consumer: Consumer, bucket: storage.Bucket, batch: list[Message]) -> None:
    """Write the batch to GCS, then commit the offsets: this order means no message is lost."""
    today = datetime.now(UTC).date()
    names = write_batch(bucket, batch, today)
    consumer.commit(asynchronous=False)
    log.info("%d message(s) écrit(s) dans %d fichier(s), offsets validés", len(batch), len(names))


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    # 30-minute batches avoid many small files; BigQuery is only refreshed every 3 hours anyway.
    parser.add_argument("--batch-size", type=int, default=10_000, help="Messages par lot.")
    parser.add_argument(
        "--batch-seconds", type=int, default=1800, help="Durée maximale d'un lot, en secondes."
    )
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s %(message)s")
    bucket = storage.Client(project=env("GOOGLE_CLOUD_PROJECT")).bucket(env("GCS_RAW_BUCKET"))
    consumer = Consumer(
        {
            "bootstrap.servers": env("KAFKA_BOOTSTRAP_SERVERS"),
            "group.id": GROUP_ID,
            # Offsets are committed manually, after writing to GCS.
            "enable.auto.commit": False,
            "auto.offset.reset": "earliest",
        }
    )
    consumer.subscribe([TOPIC])
    log.info("Lecture de %s (groupe %s, Ctrl+C pour arrêter)", TOPIC, GROUP_ID)

    batch: list[Message] = []
    batch_started = 0.0
    try:
        while True:
            message = consumer.poll(timeout=1.0)
            if message is not None:
                if message.error():
                    log.error("Erreur Kafka : %s", message.error())
                    continue
                if not batch:
                    batch_started = time.monotonic()
                batch.append(message)

            if len(batch) == 0:
                continue
            batch_is_full = len(batch) >= args.batch_size
            batch_is_old = time.monotonic() - batch_started >= args.batch_seconds
            if batch_is_full or batch_is_old:
                flush(consumer, bucket, batch)
                batch = []
    except KeyboardInterrupt:
        log.info("Arrêt demandé")
        if batch:
            flush(consumer, bucket, batch)
    finally:
        consumer.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
