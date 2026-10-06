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
Ressources GCP utilisées : voir [`infra/`](infra/README.md).

## Décisions techniques
Chaque choix est justifié dans un ADR court ([`docs/decisions/`](docs/decisions/)) :
- [0001 — Source de données : flux GBFS V'Lille](docs/decisions/0001-source-gbfs-vlille.md)
- [0002 — Outillage Python : uv, layout `src/`, pytest, ruff](docs/decisions/0002-outillage-python.md)
- [0003 — GCP : région, authentification et maîtrise des coûts](docs/decisions/0003-gcp-region-auth-couts.md)
- [0004 — Zone brute dans Cloud Storage](docs/decisions/0004-zone-brute-gcs.md)
- [0005 — Tables brutes BigQuery](docs/decisions/0005-tables-brutes-bigquery.md)
