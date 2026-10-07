# Architecture technique

Référence de ce qui compose le pipeline, ce qui tourne, quand, et où vont les données. Les choix
sont justifiés dans les [ADR](decisions/), le fonctionnement de chaque outil est expliqué dans le
[guide](guide/README.md).

## Vue d'ensemble

Une voie d'entrée par donnée :

- **disponibilités** des stations (`station_status`, les faits) : en continu, par **Kafka** ;
- **référentiel** des stations (`station_information`, la dimension) : par la collecte **batch**.

Le batch charge ensuite les deux sources dans BigQuery et reconstruit les modèles dbt.

```
DISPONIBILITÉS  API ─► producer (1 min) ─► Kafka ─► consumer (30 min) ─► GCS kafka/ ─┐
RÉFÉRENTIEL     API ─► collect ──────────────────────────────────────► GCS gbfs/  ─┼─► load ─► vlille_raw ─► dbt ─► vlille_dev
                       └───────────────── Airflow, toutes les 3 h ──────────────────┘
```

## Traitements

### Stream (en continu)

| Traitement | Commande | Quand | Entrée | Sortie |
|---|---|---|---|---|
| Producteur | `vlille-produce` | chaque minute | API `station_status` | un message par station dont l'état a changé, topic `vlille.station_status`, clé `station_id` |
| Consommateur | `vlille-consume` | lot toutes les 30 min, ou dès 10 000 messages | topic `vlille.station_status` | `gs://vlille-pipeline-raw/kafka/station_status/dt=AAAA-MM-JJ/p<partition>-<offset>.ndjson.gz` |

### Batch (DAG Airflow `vlille_pipeline`, toutes les 3 heures)

| Tâche | Commande | Entrée | Sortie |
|---|---|---|---|
| `collect` | `vlille-collect` | API `station_information` | `gs://vlille-pipeline-raw/gbfs/station_information/dt=AAAA-MM-JJ/...json.gz` |
| `load` | `vlille-load --date <hier> <aujourd'hui>` | zone brute `gbfs/` et `kafka/` | partitions du jour de `raw_station_information` et `raw_station_status_stream` |
| `dbt_build` | `dbt build` | `vlille_raw` | modèles de `vlille_dev`, 32 tests de données |

### Hors du poste

| Traitement | Quand | Effet |
|---|---|---|
| Cycle de vie Cloud Storage | en continu, côté Google | suppression des fichiers de plus de 30 jours |

## Conteneurs (Docker Compose)

Tout tourne dès que Docker Desktop est lancé (`restart: always`).

| Fichier | Service | Image | Rôle | Port du poste |
|---|---|---|---|---|
| `airflow/docker-compose.yml` | `postgres` | `postgres:16` | base d'Airflow | — |
| | `airflow-init` | `vlille-airflow:local` | migration de la base au démarrage, puis s'arrête | — |
| | `airflow-scheduler` | `vlille-airflow:local` | planifie et exécute les tâches (LocalExecutor) | — |
| | `airflow-dag-processor` | `vlille-airflow:local` | lit les DAG | — |
| | `airflow-apiserver` | `vlille-airflow:local` | interface web et API | 8081 |
| `kafka/docker-compose.yml` | `kafka` | `apache/kafka:4.3.1` | broker et contrôleur KRaft | 9092 |
| | `kafka-init` | `apache/kafka:4.3.1` | crée le topic au démarrage, puis s'arrête | — |
| | `producer` | `vlille-app:local` | `vlille-produce` | — |
| | `consumer` | `vlille-app:local` | `vlille-consume` | — |

Images construites par le projet :

- `vlille-airflow:local` ([`airflow/Dockerfile`](../airflow/Dockerfile)) : `apache/airflow:3.3.2`
  + projet installé avec uv dans un environnement séparé (`/opt/vlille/.venv`) ;
- `vlille-app:local` ([`kafka/Dockerfile`](../kafka/Dockerfile)) : `python:3.12-slim` + projet installé
  avec uv, utilisateur non-root.

Réseau Kafka : les conteneurs joignent le broker par `kafka:19092`, le poste par `localhost:9092`.

## Stockage

### Zone brute — `gs://vlille-pipeline-raw` (europe-west1)

| Préfixe | Écrit par | Format | Nom du fichier |
|---|---|---|---|
| `gbfs/station_information/dt=AAAA-MM-JJ/` | `vlille-collect` | réponse GBFS complète, gzip | dérivé de `last_updated` du flux |
| `kafka/station_status/dt=AAAA-MM-JJ/` | `vlille-consume` | une ligne JSON par message, gzip | partition et premier offset du lot |

Accès uniforme, accès public bloqué, suppression après 30 jours.

### BigQuery — dataset `vlille_raw`

| Table | Une ligne par | Partition (filtre obligatoire) |
|---|---|---|
| `raw_station_information` | fichier du référentiel | jour de `last_updated` |
| `raw_station_status_stream` | message Kafka | `ingestion_date` (jour d'écriture du consommateur) |

### BigQuery — dataset `vlille_dev` (dbt)

| Modèle | Matérialisation | Contenu |
|---|---|---|
| `stg_station_information` | vue | référentiel déplié, une ligne par station et par relevé |
| `stg_station_status` | vue | messages Kafka typés (doublons possibles) |
| `int_station_current` | vue | état le plus récent de chaque station |
| `snap_station` | snapshot | historique SCD type 2 du référentiel |
| `dim_station` | table | versions des stations avec période de validité |
| `fct_station_status` | table incrémentale (`merge`) | une ligne par remontée `(station_id, last_reported_at)`, partition par jour |
| `mart_station_daily` | table | par station et par jour : part vide, part pleine, besoin de rééquilibrage |

## Garanties

| Étape | Garantie | Mécanisme |
|---|---|---|
| Collecte du référentiel | idempotente | nom du fichier dérivé de `last_updated` : un même état réécrit le même fichier |
| Producteur → Kafka | ordre par station | clé `station_id` : une station, une partition |
| Kafka → GCS | au moins une fois | offsets validés après l'écriture dans GCS |
| Chargement BigQuery | idempotent | remplacement de la partition du jour (`WRITE_TRUNCATE`) |
| Faits | sans doublon | `MERGE` sur `(station_id, last_reported_at)` |
| Qualité | contrôlée à chaque run | validation pydantic à la collecte, 32 tests dbt |

## Configuration et accès

- Variables d'environnement lues dans `.env` (modèle : [`.env.example`](../.env.example)), y compris par
  les conteneurs.
- Accès GCP sans clé : Application Default Credentials du poste, montées en lecture seule dans les
  conteneurs Airflow et `consumer`.
- Région unique `europe-west1` ; budget de 5 € par mois avec alertes.

## Limites

- Tout ce qui tourne en continu dépend du poste allumé avec Docker Desktop lancé : les données ont des
  trous.
- Kafka : un seul broker, aucune réplication.
- BigQuery est rafraîchi toutes les 3 heures (coût) ; la collecte, elle, est continue.
- Les parts du mart sont calculées sur le nombre de remontées, approximation de la durée.
