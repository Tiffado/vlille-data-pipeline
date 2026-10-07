"""`vlille-produce`: publishes each new station report to Kafka.

Polls station_status and publishes one message per station whose `last_reported` changed. The key
is `station_id`, so all messages of a station go to the same partition and stay in order.
"""

import json
import logging
import sys
import time
from datetime import datetime

import httpx
from confluent_kafka import Producer
from pydantic import ValidationError

from vlille.client import GbfsClient, GbfsError
from vlille.models import StationStatus, StationStatusFeed
from vlille.settings import env

TOPIC = "vlille.station_status"
POLL_SECONDS = 60
HTTP_TIMEOUT_SECONDS = 10

log = logging.getLogger("vlille.produce")


def new_reports(feed: StationStatusFeed, last_seen: dict[str, datetime]) -> list[StationStatus]:
    """Return the stations with a report not seen yet, and update `last_seen`."""
    changed = []
    for station in feed.data.stations:
        if last_seen.get(station.station_id) != station.last_reported:
            changed.append(station)
            last_seen[station.station_id] = station.last_reported
    return changed


def to_message(station: StationStatus, feed_updated_at: datetime) -> bytes:
    """JSON message: the station state and the time of the feed it came from."""
    message = station.model_dump(mode="json")
    message["feed_updated_at"] = feed_updated_at.isoformat()
    return json.dumps(message).encode()


def publish(producer: Producer, stations: list[StationStatus], feed_updated_at: datetime) -> None:
    """Publish one message per station, then wait for the broker acknowledgements."""
    for station in stations:
        producer.produce(TOPIC, key=station.station_id, value=to_message(station, feed_updated_at))
    undelivered = producer.flush(timeout=30)
    if undelivered:
        log.warning("%d message(s) non confirmé(s) par le broker", undelivered)


def main() -> int:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s %(message)s")
    # acks=all: a message is acknowledged once written by all in-sync replicas.
    producer = Producer({"bootstrap.servers": env("KAFKA_BOOTSTRAP_SERVERS"), "acks": "all"})
    last_seen: dict[str, datetime] = {}

    with httpx.Client(timeout=HTTP_TIMEOUT_SECONDS) as http:
        gbfs = GbfsClient(env("VLILLE_GBFS_URL"), http)
        log.info("Publication dans %s toutes les %d s (Ctrl+C pour arrêter)", TOPIC, POLL_SECONDS)
        try:
            while True:
                try:
                    feed = gbfs.station_status()
                    changed = new_reports(feed, last_seen)
                    publish(producer, changed, feed.last_updated)
                    log.info("%d remontée(s) nouvelle(s) publiée(s)", len(changed))
                except (httpx.HTTPError, GbfsError, ValidationError) as exc:
                    # Transient source error: log it and retry on the next poll.
                    log.error("Relevé ignoré : %s", exc)
                time.sleep(POLL_SECONDS)
        except KeyboardInterrupt:
            log.info("Arrêt demandé")
    return 0


if __name__ == "__main__":
    sys.exit(main())
