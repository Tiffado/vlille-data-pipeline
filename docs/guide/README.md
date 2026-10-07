# Guide du projet

Ce guide retrace la mise en place du projet, étape par étape, dans l'ordre où elle a été faite. Chaque
chapitre explique les outils et bibliothèques utilisés, comment ils fonctionnent dans le projet, et où
regarder pour voir le résultat. Il suppose des notions de développement et de data, pas de
connaissance préalable des outils.

Les commandes pour tout lancer sont regroupées dans [RUN.md](../RUN.md). Les justifications détaillées
des choix sont dans les [ADR](../decisions/).

| # | Chapitre | Outils |
|---|---|---|
| 1 | [Le projet et les données](01-projet-et-donnees.md) | GBFS, API V'Lille |
| 2 | [Environnement de travail](02-environnement.md) | uv, Docker, gcloud, GCP, GitHub Actions |
| 3 | [Collecte et zone brute](03-collecte-zone-brute.md) | httpx, pydantic, Cloud Storage |
| 4 | [Chargement dans BigQuery](04-bigquery.md) | BigQuery |
| 5 | [Modélisation avec dbt](05-dbt.md) | dbt Core |
| 6 | [Orchestration avec Airflow](06-airflow.md) | Airflow, Docker Compose |
| 7 | [Temps réel avec Kafka](07-kafka.md) | Kafka, confluent-kafka |
| 8 | [Qualité : tests et CI](08-qualite.md) | pytest, ruff, tests dbt, GitHub Actions |

## Vocabulaire utile

| Terme | Sens dans ce projet |
|---|---|
| Zone brute | Stockage des données telles que reçues de la source, sans transformation |
| Partition | Découpage d'une table ou d'un dossier par jour : une requête ne lit que les jours utiles |
| Idempotence | Relancer une étape donne le même résultat, sans doublon |
| Schema-on-read | Le schéma est appliqué à la lecture (JSON brut interprété par dbt) |
| Schema-on-write | Le schéma est imposé à l'écriture (validation pydantic à la collecte) |
| SCD type 2 | Historisation d'une dimension : chaque changement crée une nouvelle version datée |
| DAG | Graphe de tâches avec dépendances, sans cycle (Airflow, et le graphe des modèles dbt) |
