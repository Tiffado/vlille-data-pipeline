# 0006 — dbt Core : projet, connexion et couche staging

- Date : 2026-10-07
- Statut : accepté

## Contexte
Les tables brutes contiennent une ligne par fichier avec la réponse JSON complète. Il faut une ligne par
station, des colonnes typées et des contrôles de qualité, le tout versionné et testable.

## Décision
- **dbt Core** (adaptateur BigQuery) dans le même environnement uv que le code Python, projet dans
  `dbt/`.
- Connexion `method: oauth` : dbt utilise les Application Default Credentials ; `profiles.yml` est
  versionné car il ne contient aucun secret (projet lu dans `GOOGLE_CLOUD_PROJECT`).
- Modèles dans le dataset `vlille_dev`.
- Couche **staging** matérialisée en vues : `stg_station_status` et `stg_station_information`, une
  ligne par station et par relevé, JSON déplié avec `UNNEST(JSON_QUERY_ARRAY(...))` et typé.
- Filtre de date explicite (`var('start_date')`) dans chaque modèle de staging, imposé par le filtre de
  partition obligatoire des tables brutes.
- Tests : `not_null` sur les colonnes clés, `relationships` entre statut et référentiel, test singulier
  d'unicité d'une station par relevé.

## Justification
- Vues en staging : pas de stockage dupliqué, toujours à jour ; le volume ne justifie pas de tables.
- Un seul environnement Python : une seule commande d'installation (`uv sync`).
- Tests écrits avec les modèles : une anomalie de la source fait échouer `dbt build`.

## Alternatives écartées
- dbt Cloud : service payant, hors du cadre local du projet.
- Environnement Python séparé pour dbt : plus robuste aux conflits de versions, mais deux
  environnements à gérer ; à reconsidérer si les conflits se multiplient.
- Paquet `dbt_utils` pour les tests composites : un test singulier en SQL suffit.

## Conséquences
- dbt-bigquery impose `google-cloud-storage < 3.2` : la contrainte du projet a été assouplie
  (`>= 2.18`), sans impact sur le code.
- Une même remontée de station peut apparaître dans plusieurs relevés (station sans nouvelle
  information entre deux relevés) : le dédoublonnage est traité dans la couche suivante.
