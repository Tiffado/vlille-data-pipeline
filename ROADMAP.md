# Feuille de route

Projet personnel d'apprentissage. Une case cochée = étape réalisée et vérifiée.

## Phase 0 — Mise en place
- [x] 0.1 Outils locaux : uv, CLI gcloud, Docker Desktop
- [x] 0.2 Projet GCP : facturation, budget avec alertes, API BigQuery et Cloud Storage
- [x] 0.3 Squelette du dépôt : packaging Python, `.gitignore`, `.env.example`, README, premiers ADR
- [x] 0.4 CI GitHub Actions : lint et tests sur chaque PR

## Phase 1 — Batch et modélisation
- [x] 1.1 Client GBFS V'Lille : collecte, validation, tests
- [x] 1.2 Zone brute GCS : réponses archivées telles que reçues, partitionnées par jour
- [x] 1.3 Chargement dans BigQuery : table partitionnée
- [x] 1.4 dbt : staging et tests
- [x] 1.5 dbt : snapshot SCD2 des stations et faits incrémentaux
- [x] 1.6 dbt : mart des stations vides ou pleines

## Phase 2 — Orchestration
- [x] 2.1 Airflow sous Docker Compose : DAG collecte → chargement → `dbt build`

## Phase 3 — Temps réel
- [ ] 3.1 Kafka local et producteur
- [ ] 3.2 Consommateur vers GCS

## Finalisation
- [ ] README avec schéma d'architecture, dépôt public
