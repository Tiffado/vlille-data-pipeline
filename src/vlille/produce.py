"""Commande `vlille-produce` : publie dans Kafka chaque nouvelle remontée de station.

Le flux station_status est interrogé à intervalle régulier. Un message est publié pour chaque
station dont `last_reported` a changé depuis le passage précédent, avec `station_id` comme clé :
tous les messages d'une station vont dans la même partition, donc restent dans l'ordre.
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
    """Retourne les stations dont la remontée n'a pas encore été vue, et met à jour `last_seen`."""
    changed = []
    for station in feed.data.stations:
        if last_seen.get(station.station_id) != station.last_reported:
            changed.append(station)
            last_seen[station.station_id] = station.last_reported
    return changed


def to_message(station: StationStatus, feed_updated_at: datetime) -> bytes:
    """Message JSON : l'état de la station et l'horodatage du relevé qui l'a fourni."""
    message = station.model_dump(mode="json")
    message["feed_updated_at"] = feed_updated_at.isoformat()
    return json.dumps(message).encode()


def publish(producer: Producer, stations: list[StationStatus], feed_updated_at: datetime) -> None:
    """Publie un message par station, puis attend la confirmation du broker."""
    for station in stations:
        producer.produce(TOPIC, key=station.station_id, value=to_message(station, feed_updated_at))
    undelivered = producer.flush(timeout=30)
    if undelivered:
        log.warning("%d message(s) non confirmé(s) par le broker", undelivered)


def main() -> int:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s %(message)s")
    # acks=all : un message n'est confirmé qu'une fois écrit par toutes les répliques en ligne.
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
                    # Erreur passagère de la source : journalisée, nouvel essai au tour suivant.
                    log.error("Relevé ignoré : %s", exc)
                time.sleep(POLL_SECONDS)
        except KeyboardInterrupt:
            log.info("Arrêt demandé")
    return 0


if __name__ == "__main__":
    sys.exit(main())
