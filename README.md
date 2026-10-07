# V'Lille — pipeline de données

Projet personnel d'apprentissage : collecte de la disponibilité des stations V'Lille (open data de la
Métropole Européenne de Lille), modélisée dans BigQuery avec dbt, orchestrée avec Airflow, puis
collectée en temps réel avec Kafka.

Avancement : voir [ROADMAP.md](ROADMAP.md).

## Démarrage
Prérequis : [uv](https://docs.astral.sh/uv/).
```bash
uv sync
uv run pytest
```

Collecte (une exécution) : copier `.env.example` en `.env`, s'authentifier avec
`gcloud auth application-default login`, puis :
```bash
uv run --env-file .env vlille-collect
```
La commande archive les flux `station_information` et `station_status` dans la zone brute GCS, puis
les valide ; elle se termine en erreur si un flux est invalide.

Chargement d'un jour dans les tables brutes BigQuery (remplace la partition du jour) :
```bash
uv run --env-file .env vlille-load --date 2026-10-06
```
Modèles dbt (dans `dbt/`, dataset `vlille_dev`) :
- `stg_station_status`, `stg_station_information` : JSON brut déplié, une ligne par station et par relevé ;
- `snap_station` : historique SCD type 2 du référentiel des stations ;
- `fct_station_status` : une ligne par remontée de station, table incrémentale ;
- `dim_station` : versions des stations avec leur période de validité ;
- `mart_station_daily` : par station et par jour, part du temps vide ou pleine (approximée par la part
  des remontées) et besoin de rééquilibrage.

Construction des modèles, du snapshot et tests de données :
```bash
uv run --env-file .env dbt build --project-dir dbt --profiles-dir dbt
```

## Orchestration (Airflow)
Airflow tourne en local sous Docker Compose (Docker Desktop requis). Le DAG `vlille_pipeline` enchaîne
toutes les 30 minutes la collecte, le chargement (hier et aujourd'hui) et `dbt build`.
```bash
docker compose -f airflow/docker-compose.yml up -d --build
```
Interface : http://localhost:8080 (usage local, sans authentification). Arrêt :
`docker compose -f airflow/docker-compose.yml down`.

Ressources GCP utilisées : voir [`infra/`](infra/README.md).

## Décisions techniques
Chaque choix est justifié dans un ADR court ([`docs/decisions/`](docs/decisions/)) :
- [0001 — Source de données : flux GBFS V'Lille](docs/decisions/0001-source-gbfs-vlille.md)
- [0002 — Outillage Python : uv, layout `src/`, pytest, ruff](docs/decisions/0002-outillage-python.md)
- [0003 — GCP : région, authentification et maîtrise des coûts](docs/decisions/0003-gcp-region-auth-couts.md)
- [0004 — Zone brute dans Cloud Storage](docs/decisions/0004-zone-brute-gcs.md)
- [0005 — Tables brutes BigQuery](docs/decisions/0005-tables-brutes-bigquery.md)
- [0006 — dbt Core : projet, connexion et couche staging](docs/decisions/0006-dbt-staging.md)
- [0007 — Snapshot SCD2 des stations et faits incrémentaux](docs/decisions/0007-snapshot-et-faits-incrementaux.md)
- [0008 — Mart de saturation quotidienne des stations](docs/decisions/0008-mart-saturation-quotidienne.md)
- [0009 — Orchestration avec Airflow en local](docs/decisions/0009-orchestration-airflow.md)
