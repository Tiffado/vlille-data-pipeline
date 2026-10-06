"""Commande `vlille-collect` : collecte les flux GBFS, les archive dans la zone brute, les valide.

L'archivage précède la validation : une réponse invalide est conservée telle que reçue, mais la
commande se termine en erreur pour la signaler.
"""

import logging
import os
import sys

import httpx
from google.cloud import storage
from pydantic import BaseModel, ValidationError

from vlille.client import GbfsClient
from vlille.models import StationInformationFeed, StationStatusFeed
from vlille.raw_store import RawStore

FEEDS: dict[str, type[BaseModel]] = {
    "station_information": StationInformationFeed,
    "station_status": StationStatusFeed,
}
HTTP_TIMEOUT_SECONDS = 10

log = logging.getLogger("vlille.collect")


def collect(gbfs: GbfsClient, store: RawStore) -> bool:
    """Archive puis valide chaque flux. Retourne False si au moins un flux est invalide."""
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


def _env(name: str) -> str:
    value = os.environ.get(name)
    if not value:
        raise SystemExit(f"Variable d'environnement manquante : {name} (voir .env.example)")
    return value


def main() -> int:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s %(message)s")
    bucket = storage.Client(project=_env("GOOGLE_CLOUD_PROJECT")).bucket(_env("GCS_RAW_BUCKET"))
    with httpx.Client(timeout=HTTP_TIMEOUT_SECONDS) as http:
        gbfs = GbfsClient(_env("VLILLE_GBFS_URL"), http)
        return 0 if collect(gbfs, RawStore(bucket)) else 1


if __name__ == "__main__":
    sys.exit(main())
