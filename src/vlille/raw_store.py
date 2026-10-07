"""Archives raw GBFS responses in the Cloud Storage raw zone.

The object name comes from the feed's `last_updated`: collecting the same state twice rewrites the
same object with the same content, so there are no duplicates.
"""

import gzip
import json
from datetime import UTC, datetime

from google.cloud.storage import Bucket

from vlille.paths import GBFS_PREFIX


class RawStoreError(Exception):
    """The response has no readable `last_updated`, so it cannot be named."""


def object_name(feed: str, last_updated: datetime) -> str:
    """e.g. gbfs/station_information/dt=2026-10-06/station_information_20261006T151202Z.json.gz"""
    utc = last_updated.astimezone(UTC)
    day = utc.strftime("%Y-%m-%d")
    timestamp = utc.strftime("%Y%m%dT%H%M%SZ")
    return f"{GBFS_PREFIX}/{feed}/dt={day}/{feed}_{timestamp}.json.gz"


def read_last_updated(payload: bytes) -> datetime:
    """Read only `last_updated` (epoch seconds); the rest is validated elsewhere."""
    try:
        epoch = json.loads(payload)["last_updated"]
        return datetime.fromtimestamp(int(epoch), tz=UTC)
    except (ValueError, KeyError, TypeError) as exc:
        raise RawStoreError("Champ last_updated absent ou illisible") from exc


class RawStore:
    def __init__(self, bucket: Bucket) -> None:
        self._bucket = bucket

    def write(self, feed: str, payload: bytes) -> str:
        """Archive a raw response and return the object name."""
        name = object_name(feed, read_last_updated(payload))
        blob = self._bucket.blob(name)
        blob.upload_from_string(gzip.compress(payload), content_type="application/gzip")
        return name
