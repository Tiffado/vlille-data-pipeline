"""Dépôt des réponses GBFS brutes dans la zone brute Cloud Storage.

Chaque réponse est stockée telle que reçue, compressée en gzip, sous un nom déduit de son champ
`last_updated` : deux collectes du même état produisent le même objet (idempotence). Un objet déjà
présent n'est jamais réécrit (zone brute immuable).
"""

import gzip
import json
from datetime import UTC, datetime

from google.api_core.exceptions import PreconditionFailed
from google.cloud.storage import Bucket

PREFIX = "gbfs"


class RawStoreError(Exception):
    """La réponse ne permet pas de construire un nom d'objet (ex. `last_updated` illisible)."""


def object_name(feed: str, last_updated: datetime) -> str:
    """Chemin de l'objet, partitionné par jour à la manière de Hive.

    Ex. gbfs/station_status/dt=2026-10-06/station_status_20261006T151202Z.json.gz
    """
    ts = last_updated.astimezone(UTC)
    return f"{PREFIX}/{feed}/dt={ts:%Y-%m-%d}/{feed}_{ts:%Y%m%dT%H%M%SZ}.json.gz"


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

    def write(self, feed: str, payload: bytes) -> tuple[str, bool]:
        """Archive une réponse brute.

        Retourne (nom de l'objet, True si écrit / False s'il existait déjà).
        """
        name = object_name(feed, read_last_updated(payload))
        # mtime=0 : même contenu → mêmes octets compressés, quelle que soit l'heure de collecte.
        data = gzip.compress(payload, mtime=0)
        try:
            # if_generation_match=0 : écrire seulement si l'objet n'existe pas encore.
            self._bucket.blob(name).upload_from_string(
                data, content_type="application/gzip", if_generation_match=0
            )
        except PreconditionFailed:
            return name, False
        return name, True
