# Feuille de route

Projet personnel d'apprentissage. Une case cochée = étape réalisée et vérifiée.

## Phase 0 — Mise en place
- [x] 0.1 Outils locaux : uv, CLI gcloud, Docker Desktop
- [x] 0.2 Projet GCP : facturation, budget avec alertes, API BigQuery et Cloud Storage
- [ ] 0.3 Squelette du dépôt : packaging Python, `.gitignore`, `.env.example`, README, premiers ADR
- [ ] 0.4 CI GitHub Actions : lint et tests sur chaque PR

## Phase 1 — Ingestion batch et modélisation dbt
- [ ] 1.1 Client GBFS V'Lille : collecte, validation, tests
- [ ] 1.2 Zone brute GCS : JSON compressé partitionné par date, cycle de vie
- [ ] 1.3 Tables BigQuery partitionnées et clusterisées, filtre de partition obligatoire
- [ ] 1.4 Collecte météo Open-Meteo
- [ ] 1.5 dbt Core : sources, staging, tests
- [ ] 1.6 Snapshot SCD2 des stations
- [ ] 1.7 Faits incrémentaux dédupliqués sur `(station_id, last_reported)`
- [ ] 1.8 Marts : stations vides ou pleines, rééquilibrage, effet de la météo
- [ ] 1.9 CI : `dbt build` sur un dataset BigQuery dédié

## Phase 2 — Orchestration Airflow
- [ ] 2.0 Image Docker du collecteur : Dockerfile multi-étapes avec uv, utilisateur non-root
- [ ] 2.1 Airflow local sous Docker Compose
- [ ] 2.2 DAG météo, snapshot et build dbt, contrôles qualité ; collecte lancée dans le conteneur du collecteur
- [ ] 2.3 Backfill et rejeux idempotents

## Phase 3 — Temps réel Kafka
- [ ] 3.1 Kafka local sous Docker (mode KRaft)
- [ ] 3.2 Producteur : statut des stations, clé `station_id`
- [ ] 3.3 Consommateur vers GCS et BigQuery, commit des offsets après écriture (at-least-once)
- [ ] 3.4 Gestion des messages invalides et relance

## Phase 4 — Options
- [ ] 4.1 API FastAPI au-dessus des marts
- [ ] 4.2 Recalcul historique PySpark sur Dataproc Serverless
- [ ] 4.3 Infrastructure Terraform

## Finalisation
- [ ] README final : schéma d'architecture, choix justifiés, fait / prévu / hors périmètre
- [ ] Dépôt public
