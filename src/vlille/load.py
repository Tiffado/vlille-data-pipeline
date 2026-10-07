"""`vlille-load`: loads one day of the GCS raw zone into the BigQuery raw tables.

Each run replaces the day's partition, so loading a day twice gives the same result.
"""

import argparse
import gzip
import json
import logging
import sys
from datetime import UTC, date, datetime

from google.cloud import bigquery, storage

from vlille.paths import GBFS_PREFIX, KAFKA_PREFIX
from vlille.raw_store import read_last_updated
from vlille.settings import env

# Same schemas as in infra/. Without them, BigQuery would infer `payload` as a RECORD, not JSON.
RAW_SCHEMA = [
    bigquery.SchemaField("last_updated", "TIMESTAMP", mode="REQUIRED"),
    bigquery.SchemaField("source_uri", "STRING", mode="REQUIRED"),
    bigquery.SchemaField("payload", "JSON", mode="REQUIRED"),
]
STREAM_SCHEMA = [
    bigquery.SchemaField("ingestion_date", "DATE", mode="REQUIRED"),
    bigquery.SchemaField("source_uri", "STRING", mode="REQUIRED"),
    bigquery.SchemaField("payload", "JSON", mode="REQUIRED"),
]

log = logging.getLogger("vlille.load")


def read_station_information(bucket: storage.Bucket, day: date) -> list[dict]:
    """One row per reference data file of the day."""
    rows = []
    prefix = f"{GBFS_PREFIX}/station_information/dt={day.isoformat()}/"
    for blob in bucket.list_blobs(prefix=prefix):
        payload = gzip.decompress(blob.download_as_bytes())
        rows.append(
            {
                "last_updated": read_last_updated(payload).isoformat(),
                "source_uri": f"gs://{bucket.name}/{blob.name}",
                "payload": json.loads(payload),
            }
        )
    return rows


def read_station_events(bucket: storage.Bucket, day: date) -> list[dict]:
    """One row per Kafka message written that day."""
    rows = []
    for blob in bucket.list_blobs(prefix=f"{KAFKA_PREFIX}/dt={day.isoformat()}/"):
        content = gzip.decompress(blob.download_as_bytes())
        for line in content.splitlines():
            rows.append(
                {
                    "ingestion_date": day.isoformat(),
                    "source_uri": f"gs://{bucket.name}/{blob.name}",
                    "payload": json.loads(line),
                }
            )
    return rows


def replace_partition(
    bq: bigquery.Client, table: str, day: date, rows: list[dict], schema: list
) -> int:
    """Replace the day's partition with the given rows; return the number of rows."""
    if not rows:
        log.warning("%s : aucune donnée pour le %s, partition inchangée", table, day)
        return 0
    # The $YYYYMMDD suffix targets one partition; WRITE_TRUNCATE replaces it.
    partition = f"{table}${day.strftime('%Y%m%d')}"
    job_config = bigquery.LoadJobConfig(
        source_format=bigquery.SourceFormat.NEWLINE_DELIMITED_JSON,
        schema=schema,
        write_disposition=bigquery.WriteDisposition.WRITE_TRUNCATE,
    )
    bq.load_table_from_json(rows, partition, job_config=job_config).result()
    log.info("%d ligne(s) chargée(s) dans %s", len(rows), partition)
    return len(rows)


def load_day(
    bq: bigquery.Client, bucket: storage.Bucket, dataset: str, day: date
) -> dict[str, int]:
    """Load one day into both raw tables; return the number of rows per table."""
    information = read_station_information(bucket, day)
    events = read_station_events(bucket, day)
    return {
        "raw_station_information": replace_partition(
            bq, f"{dataset}.raw_station_information", day, information, RAW_SCHEMA
        ),
        "raw_station_status_stream": replace_partition(
            bq, f"{dataset}.raw_station_status_stream", day, events, STREAM_SCHEMA
        ),
    }


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
