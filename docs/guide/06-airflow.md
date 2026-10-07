# 6. Orchestration avec Airflow

## Airflow en bref

[Apache Airflow](https://airflow.apache.org/docs/) planifie et enchaîne des traitements. Un traitement
est décrit par un **DAG** (graphe orienté sans cycle) écrit en Python : des **tâches**, leurs
**dépendances**, une **planification**, une politique de **relance**. Airflow garde l'historique de
chaque exécution et les journaux de chaque tâche, consultables dans son interface web.

## Les composants lancés

Fichier [`airflow/docker-compose.yml`](../../airflow/docker-compose.yml), version simplifiée du fichier
officiel d'Airflow 3.3 :

| Service | Rôle |
|---|---|
| `postgres` | Base d'Airflow : DAG, exécutions, états des tâches |
| `airflow-init` | Prépare la base au premier démarrage, puis s'arrête |
| `airflow-scheduler` | Décide quoi lancer et quand ; avec le *LocalExecutor*, exécute aussi les tâches |
| `airflow-dag-processor` | Lit les fichiers de DAG |
| `airflow-apiserver` | Interface web et API, sur le port 8081 du poste |

Le fichier officiel utilise Celery et Redis pour répartir les tâches sur plusieurs machines : inutile
sur un seul poste.

## L'image

[`airflow/Dockerfile`](../../airflow/Dockerfile) part de l'image officielle `apache/airflow:3.3.2` et
installe le projet avec uv dans un **environnement virtuel séparé** (`/opt/vlille/.venv`) : Airflow et
dbt imposent chacun beaucoup de versions de dépendances, les isoler évite les conflits. Le fichier
d'identifiants GCP (ADC) du poste est monté en lecture seule ; la configuration vient du `.env`.

## Le DAG `vlille_pipeline`

[`airflow/dags/vlille_pipeline.py`](../../airflow/dags/vlille_pipeline.py)

```
collect (référentiel)  ──►  load (hier et aujourd'hui)  ──►  dbt_build
```

- toutes les **3 heures** : le mart est quotidien, et dbt (modèles et tests) reste dans le quota
  gratuit de BigQuery malgré le volume des événements Kafka ;
- `load` charge le référentiel collecté et les messages écrits par le consommateur Kafka ;
- chaque tâche appelle une commande du projet (`BashOperator`) : la logique reste dans le paquet testé ;
- **2 relances** à 2 minutes d'intervalle ;
- `catchup=False` : les créneaux manqués ne sont pas rejoués, la collecte lisant l'état actuel de l'API ;
- un seul run actif à la fois.

## Pour voir

Interface : <http://localhost:8081> (sans authentification, usage local).

- **Dags → vlille_pipeline** : historique des exécutions, en vert ou rouge.
- **Graph** : les trois tâches et leurs dépendances.
- Une tâche d'un run → **Logs** : sortie de la commande (fichiers archivés, résumé de `dbt build`).
- **Trigger** (en haut à droite) : lancer un run immédiatement.

## Limites

- Airflow ne tourne que lorsque Docker Desktop est lancé.
- Une modification du code Python ou des modèles dbt demande de reconstruire l'image ; les DAG sont
  relus sans reconstruction.

Décision : [ADR 0009](../decisions/0009-orchestration-airflow.md).
