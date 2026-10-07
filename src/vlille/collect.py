"""`vlille-collect`: archives and validates the station reference data (station_information).

Station availability (station_status) comes through Kafka instead. The response is archived before
validation, so an invalid response is kept as evidence, but the command exits with an error.
"""

import logging
import sys

import httpx
from google.cloud import storage
from pydantic import BaseModel, ValidationError

from vlille.client import GbfsClient
from vlille.models import StationInformationFeed
from vlille.raw_store import RawStore
from vlille.settings import env

FEEDS: dict[str, type[BaseModel]] = {
    "station_information": StationInformationFeed,
}
HTTP_TIMEOUT_SECONDS = 10

log = logging.getLogger("vlille.collect")


def collect(gbfs: GbfsClient, store: RawStore) -> bool:
    """Archive then validate each feed. Return False if a feed is invalid."""
    all_valid = True
    for feed, model in FEEDS.items():
        raw = gbfs.fetch_raw(feed)
        name = store.write(feed, raw)
        log.info("archivé : %s", name)
        try:
            model.model_validate_json(raw)
        except ValidationError as exc:
            all_valid = False
            log.error("%s invalide : %d erreur(s)\n%s", feed, exc.error_count(), exc)
    return all_valid


def main() -> int:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s %(message)s")
    bucket = storage.Client(project=env("GOOGLE_CLOUD_PROJECT")).bucket(env("GCS_RAW_BUCKET"))
    with httpx.Client(timeout=HTTP_TIMEOUT_SECONDS) as http:
        gbfs = GbfsClient(env("VLILLE_GBFS_URL"), http)
        return 0 if collect(gbfs, RawStore(bucket)) else 1


if __name__ == "__main__":
    sys.exit(main())
