# Ressources GCP

Ressources créées en ligne de commande (projet `vlille-pipeline`, région `europe-west1`).

## Zone brute Cloud Storage
```bash
gcloud storage buckets create gs://vlille-pipeline-raw --location=europe-west1 --default-storage-class=STANDARD --uniform-bucket-level-access --public-access-prevention
gcloud storage buckets update gs://vlille-pipeline-raw --lifecycle-file=infra/gcs-lifecycle.json
```

## Tables brutes BigQuery
Partition par jour, filtre de partition obligatoire.

```bash
bq mk --dataset --location=europe-west1 vlille-pipeline:vlille_raw
```

Référentiel des stations (batch), une ligne par fichier :
```bash
bq mk --table --time_partitioning_field=last_updated --time_partitioning_type=DAY --require_partition_filter=true vlille-pipeline:vlille_raw.raw_station_information infra/raw_table_schema.json
```

Disponibilités (Kafka), une ligne par message :
```bash
bq mk --table --time_partitioning_field=ingestion_date --time_partitioning_type=DAY --require_partition_filter=true vlille-pipeline:vlille_raw.raw_station_status_stream infra/stream_table_schema.json
```
