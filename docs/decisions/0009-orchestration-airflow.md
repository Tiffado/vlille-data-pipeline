# 0009 — Orchestration avec Airflow en local

- Date : 2026-10-07
- Statut : accepté

## Contexte
La collecte, le chargement et les modèles dbt sont trois commandes à enchaîner dans l'ordre. Le snapshot
SCD2 doit tourner à chaque chargement. Jusqu'ici, une tâche du Planificateur Windows lançait seulement la
collecte.

## Décision
- **Airflow 3.3** sous Docker Compose (`airflow/`), version simplifiée du fichier officiel :
  LocalExecutor, PostgreSQL, scheduler, dag-processor, api-server ; pas de Celery ni de Redis.
- **Image dérivée** de l'image officielle : le projet y est installé avec uv dans un environnement
  virtuel séparé (`/opt/vlille/.venv`).
- **DAG `vlille_pipeline`**, toutes les 30 minutes : `collect` → `load` (hier et aujourd'hui) →
  `dbt_build`, en `BashOperator` qui appellent les commandes du projet ; 2 relances à 2 minutes
  d'intervalle ; `catchup=False`, un seul run actif à la fois.
- Identifiants GCP : fichier des Application Default Credentials monté en lecture seule ; configuration
  lue dans le `.env` du projet.
- Authentification de l'interface désactivée (tout utilisateur est administrateur) : usage local
  uniquement.
- La tâche du Planificateur Windows et son script sont retirés.

## Justification
- LocalExecutor : un seul poste, pas besoin d'exécution distribuée.
- Environnement séparé : Airflow et dbt épinglent chacun beaucoup de dépendances ; les isoler évite les
  conflits de versions.
- `BashOperator` sur les commandes existantes : le DAG ne fait qu'orchestrer, la logique reste dans le
  paquet testé.
- `catchup=False` et date d'exécution : la collecte lit l'état actuel de l'API, rejouer un créneau passé
  n'a pas de sens.

## Alternatives écartées
- Cloud Composer : Airflow managé, plusieurs centaines d'euros par mois.
- docker-compose officiel complet (CeleryExecutor) : architecture distribuée inutile ici.
- Installer le projet dans l'environnement d'Airflow : conflits de dépendances.

## Conséquences
- Airflow ne tourne que lorsque Docker Desktop est lancé sur le poste : ce n'est pas un serveur.
- Une modification du code ou des modèles dbt demande de reconstruire l'image
  (`docker compose ... up -d --build`) ; les DAG sont montés et relus sans reconstruction.
