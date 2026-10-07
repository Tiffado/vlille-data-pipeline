"""Commande `vlille-load` : charge un jour de la zone brute GCS dans les tables brutes BigQuery.

Chaque fichier devient une ligne (horodatage, chemin d'origine, réponse JSON complète). La partition
du jour est remplacée entièrement : recharger un jour donne toujours le même résultat (idempotence).
"""

import argparse
import gzip
import json
import logging
import sys
from datetime import UTC, date, datetime

from google.cloud import bigquery, storage

from vlille.raw_store import PREFIX, read_last_updated
from vlille.settings import env

FEEDS = ("station_information", "station_status")

# Schéma des tables brutes (identique à infra/raw_table_schema.json). Sans schéma explicite,
# BigQuery déduirait `payload` comme une structure imbriquée au lieu d'une colonne JSON.
RAW_SCHEMA = [
    bigquery.SchemaField("last_updated", "TIMESTAMP", mode="REQUIRED"),
    bigquery.SchemaField("source_uri", "STRING", mode="REQUIRED"),
    bigquery.SchemaField("payload", "JSON", mode="REQUIRED"),
]

log = logging.getLogger("vlille.load")


def read_day(bucket: storage.Bucket, feed: str, day: date) -> list[dict]:
    """Lit les fichiers d'un flux pour un jour et les convertit en lignes de la table brute."""
    rows = []
    for blob in bucket.list_blobs(prefix=f"{PREFIX}/{feed}/dt={day.isoformat()}/"):
        payload = gzip.decompress(blob.download_as_bytes())
        rows.append(
            {
                "last_updated": read_last_updated(payload).isoformat(),
                "source_uri": f"gs://{bucket.name}/{blob.name}",
                "payload": json.loads(payload),
            }
        )
    return rows


def load_day(
    bq: bigquery.Client, bucket: storage.Bucket, dataset: str, day: date
) -> dict[str, int]:
    """Remplace la partition du jour de chaque table brute.

    Retourne le nombre de lignes chargées par flux.
    """
    loaded = {}
    for feed in FEEDS:
        rows = read_day(bucket, feed, day)
        if not rows:
            log.warning("%s : aucun fichier pour le %s, partition inchangée", feed, day)
            loaded[feed] = 0
            continue
        # Le suffixe $AAAAMMJJ cible une seule partition ; WRITE_TRUNCATE la remplace.
        table = f"{dataset}.raw_{feed}${day.strftime('%Y%m%d')}"
        job_config = bigquery.LoadJobConfig(
            source_format=bigquery.SourceFormat.NEWLINE_DELIMITED_JSON,
            schema=RAW_SCHEMA,
            write_disposition=bigquery.WriteDisposition.WRITE_TRUNCATE,
        )
        bq.load_table_from_json(rows, table, job_config=job_config).result()
        log.info("%s : %d ligne(s) chargée(s) dans %s", feed, len(rows), table)
        loaded[feed] = len(rows)
    return loaded


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument(
        "--date",
        type=date.fromisoformat,
        nargs="+",
        default=[datetime.now(UTC).date()],
        help="Jour(s) à charger, AAAA-MM-JJ (UTC). Par défaut : aujourd'hui.",
    )
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s %(message)s")
    project = env("GOOGLE_CLOUD_PROJECT")
    bucket = storage.Client(project=project).bucket(env("GCS_RAW_BUCKET"))
    bq = bigquery.Client(project=project)
    for day in args.date:
        load_day(bq, bucket, f"{project}.{env('BQ_DATASET_RAW')}", day)
    return 0


if __name__ == "__main__":
    sys.exit(main())
