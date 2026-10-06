# Ressources GCP

Ressources créées en ligne de commande (projet `vlille-pipeline`, région `europe-west1`).

## Zone brute Cloud Storage
```bash
gcloud storage buckets create gs://vlille-pipeline-raw --location=europe-west1 --default-storage-class=STANDARD --uniform-bucket-level-access --public-access-prevention
gcloud storage buckets update gs://vlille-pipeline-raw --lifecycle-file=infra/gcs-lifecycle.json
```

## Tables brutes BigQuery
Une ligne par fichier de la zone brute ; partition par jour sur `last_updated`, filtre de partition
obligatoire.
```bash
bq mk --dataset --location=europe-west1 vlille-pipeline:vlille_raw
bq mk --table --time_partitioning_field=last_updated --time_partitioning_type=DAY --require_partition_filter=true vlille-pipeline:vlille_raw.raw_station_status infra/raw_table_schema.json
bq mk --table --time_partitioning_field=last_updated --time_partitioning_type=DAY --require_partition_filter=true vlille-pipeline:vlille_raw.raw_station_information infra/raw_table_schema.json
```
