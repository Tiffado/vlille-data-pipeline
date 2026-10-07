# 4. Chargement dans BigQuery

## BigQuery en bref

[BigQuery](https://cloud.google.com/bigquery/docs) est l'entrepôt de données de Google Cloud : on y
écrit du SQL, Google gère les machines. Les données sont rangées en **datasets** (équivalent d'un
schéma) qui contiennent des **tables**. La facturation porte sur le stockage et sur le **volume lu**
par chaque requête : la console affiche ce volume avant l'exécution.

## Les tables brutes

Dataset `vlille_raw`, une table par source :

| Table | Une ligne par | Partition | Colonnes |
|---|---|---|---|
| `raw_station_information` | fichier du référentiel (batch) | jour de `last_updated` | `last_updated`, `source_uri`, `payload` (JSON) |
| `raw_station_status_stream` | message Kafka (état d'une station) | `ingestion_date`, jour d'écriture par le consommateur | `ingestion_date`, `source_uri`, `payload` (JSON) |

- **Partition par jour** : une requête filtrée sur un jour ne lit que ce jour.
- **Filtre de partition obligatoire** : BigQuery refuse une requête qui lirait toute la table par
  oubli. C'est le garde-fou de coût.
- Le JSON n'est pas découpé au chargement : c'est dbt qui l'interprète (*schema-on-read*). Un champ
  ajouté par la source ne casse pas le chargement.
- La table des événements est partitionnée par **date d'arrivée**, comme souvent pour un flux : le
  dossier `dt=` du consommateur correspond exactement à une partition.

Les commandes de création sont dans [`infra/README.md`](../../infra/README.md).

## Ce que fait `vlille-load`

Pour chaque jour demandé : lire les fichiers `dt=AAAA-MM-JJ` de la zone brute (référentiel et
messages Kafka), et **remplacer** la partition de ce jour dans chaque table (*load job* en mode `WRITE_TRUNCATE` sur
`table$AAAAMMJJ`). Recharger un jour donne toujours le même résultat : c'est l'équivalent d'un
`INSERT OVERWRITE PARTITION` en Hive.

Les *load jobs* sont gratuits. Le schéma est donné explicitement : sans lui, BigQuery devinait que
`payload` était une structure imbriquée au lieu d'une colonne JSON, et refusait le chargement.

Bibliothèque : [google-cloud-bigquery](https://cloud.google.com/python/docs/reference/bigquery/latest).
Code : [`load.py`](../../src/vlille/load.py).

```bash
uv run --env-file .env vlille-load --date 2026-10-06 2026-10-07
```

## Pour voir

- BigQuery Studio : <https://console.cloud.google.com/bigquery?project=vlille-pipeline>
  - `vlille_raw` → une table → onglets **Schéma**, **Détails** (partitionnement), **Aperçu** (gratuit) ;
  - **Historique des jobs** en bas de page : les chargements, leur mode et leur durée.
- Une requête qui lit les événements du jour :

```sql
SELECT
  STRING(payload.station_id) AS station_id,
  INT64(payload.num_bikes_available) AS velos,
  TIMESTAMP(STRING(payload.last_reported)) AS remontee
FROM vlille_raw.raw_station_status_stream
WHERE ingestion_date = CURRENT_DATE()
```

Décision : [ADR 0005](../decisions/0005-tables-brutes-bigquery.md).
