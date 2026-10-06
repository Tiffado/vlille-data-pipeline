# V'Lille — pipeline de données

Projet personnel d'apprentissage : collecte de la disponibilité des stations V'Lille (open data de la
Métropole Européenne de Lille), enrichie avec la météo, modélisée dans BigQuery avec dbt.

Avancement : voir [ROADMAP.md](ROADMAP.md).

## Démarrage
Prérequis : [uv](https://docs.astral.sh/uv/).
```bash
uv sync
uv run pytest
```

## Décisions techniques
Chaque choix est justifié dans un ADR court ([`docs/decisions/`](docs/decisions/)) :
- [0001 — Source de données : flux GBFS V'Lille](docs/decisions/0001-source-gbfs-vlille.md)
- [0002 — Outillage Python : uv, layout `src/`, pytest, ruff](docs/decisions/0002-outillage-python.md)
- [0003 — GCP : région, authentification et maîtrise des coûts](docs/decisions/0003-gcp-region-auth-couts.md)
