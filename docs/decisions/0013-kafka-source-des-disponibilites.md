# 0013 — Kafka, seule source des disponibilités

- Date : 2026-10-07
- Statut : accepté (modifie les ADR 0005, 0009, 0010 et 0011)

## Contexte
La collecte batch et le producteur Kafka interrogeaient tous deux le flux `station_status` et
écrivaient tous deux dans la zone brute ; seules les données du batch atteignaient BigQuery. Deux voies
d'entrée pour la même donnée, dont une sans usage : une architecture incohérente.

## Décision
- **Une seule voie d'entrée par donnée** :
  - disponibilités (`station_status`) : uniquement par Kafka (producteur → topic → consommateur →
    `kafka/station_status/` dans la zone brute) ;
  - référentiel (`station_information`) : uniquement par la collecte batch (`gbfs/`).
- Nouvelle table brute **`raw_station_status_stream`** : une ligne par message, partitionnée par
  `ingestion_date` (jour d'écriture par le consommateur), filtre de partition obligatoire.
- `vlille-load` charge, pour chaque jour, le référentiel et les messages Kafka (remplacement de la
  partition du jour).
- `stg_station_status` lit uniquement le flux ; `fct_station_status` relit les deux derniers jours de
  partitions et fusionne sur `(station_id, last_reported_at)`, ce qui élimine les doublons du
  « au moins une fois ».
- DAG Airflow toutes les **3 heures** (au lieu de 30 minutes).
- L'ancienne table `raw_station_status` (photos du batch) n'est plus utilisée.

## Justification
- Une source par donnée : pas de recouvrement, pas de réconciliation entre deux voies.
- Données plus fines : chaque changement d'état d'une station, au lieu d'une photo par demi-heure.
- 3 heures : environ 100 000 messages par jour ; reconstruire et tester les modèles toutes les
  30 minutes ferait dépasser le quota gratuit de requêtes BigQuery en quelques semaines. Le mart étant
  quotidien, la fraîcheur reste suffisante.
- Partition par date d'arrivée : un dossier `dt=` du consommateur correspond exactement à une partition,
  ce qui garde le chargement idempotent.

## Alternatives écartées
- Garder les deux voies : incohérent, données dupliquées.
- Réunir l'historique batch et le flux dans le staging : complexité durable pour quelques heures
  d'historique.
- Écrire directement dans BigQuery depuis le consommateur (streaming) : coût et complexité
  supplémentaires, et la zone brute ne serait plus la source unique.

## Conséquences
- L'historique des disponibilités commence avec la collecte Kafka (2026-10-07).
- BigQuery est rafraîchi toutes les 3 heures ; la collecte reste continue.
- Un message arrivé plus de deux jours après son écriture demande une reconstruction complète
  (`dbt build --full-refresh`).
