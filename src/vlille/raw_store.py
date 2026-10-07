"""Dépôt des réponses GBFS brutes dans la zone brute Cloud Storage.

Chaque réponse est stockée telle que reçue, compressée en gzip, sous un nom déduit de son champ
`last_updated` : deux collectes du même état écrivent le même objet, la seconde remplaçant la
première par un contenu identique (idempotence, pas de doublon).
"""

import gzip
import json
from datetime import UTC, datetime

from google.cloud.storage import Bucket

PREFIX = "gbfs"


class RawStoreError(Exception):
    """La réponse ne permet pas de construire un nom d'objet (ex. `last_updated` illisible)."""


def object_name(feed: str, last_updated: datetime) -> str:
    """Chemin de l'objet, partitionné par jour à la manière de Hive.

    Ex. gbfs/station_status/dt=2026-10-06/station_status_20261006T151202Z.json.gz
    """
    utc = last_updated.astimezone(UTC)
    day = utc.strftime("%Y-%m-%d")
    timestamp = utc.strftime("%Y%m%dT%H%M%SZ")
    return f"{PREFIX}/{feed}/dt={day}/{feed}_{timestamp}.json.gz"


def read_last_updated(payload: bytes) -> datetime:
    """Lit seulement `last_updated` (secondes epoch) ; le reste du contenu n'est pas validé ici."""
    try:
        epoch = json.loads(payload)["last_updated"]
        return datetime.fromtimestamp(int(epoch), tz=UTC)
    except (ValueError, KeyError, TypeError) as exc:
        raise RawStoreError("Champ last_updated absent ou illisible") from exc


class RawStore:
    """Écrit dans un bucket fourni de l'extérieur (vrai bucket GCS, ou faux bucket en test)."""

    def __init__(self, bucket: Bucket) -> None:
        self._bucket = bucket

    def write(self, feed: str, payload: bytes) -> str:
        """Archive une réponse brute et retourne le nom de l'objet écrit."""
        name = object_name(feed, read_last_updated(payload))
        blob = self._bucket.blob(name)
        blob.upload_from_string(gzip.compress(payload), content_type="application/gzip")
        return name
