# 0007 — Snapshot SCD2 des stations et faits incrémentaux

- Date : 2026-10-07
- Statut : accepté

## Contexte
Le référentiel des stations peut changer (nom, capacité, position) et l'analyse doit utiliser l'état
valable à la date observée. Côté disponibilité, une station sans nouvelle remontée entre deux relevés
apparaît plusieurs fois avec la même information (1 602 lignes pour 1 396 remontées réelles le
2026-10-06).

## Décision
- **`snap_station`** : snapshot dbt (SCD type 2) alimenté par `int_station_current` (état le plus
  récent de chaque station), stratégie `check` sur nom, capacité, latitude et longitude.
- **`fct_station_status`** : table incrémentale, une ligne par remontée `(station_id,
  last_reported_at)`, stratégie `merge` sur cette clé, partitionnée par jour sur `last_reported_at`.
- En incrémental, relecture des relevés des 24 dernières heures.

## Justification
- Stratégie `check` : le flux n'a pas de date de modification par station (`last_updated` change à
  chaque relevé), on compare donc les colonnes métier.
- Incrémental plutôt que table complète : le coût ne croît pas avec l'historique.
- Marge de 24 heures + fusion sur la clé : un relevé chargé en retard est rattrapé sans doublon ;
  relancer donne le même résultat (vérifié : deux exécutions, même nombre de lignes).

## Alternatives écartées
- Stratégie `timestamp` du snapshot : chaque relevé créerait une nouvelle version sans changement réel.
- Stratégie incrémentale `append` : plus simple mais crée des doublons en cas de relecture.

## Conséquences
- Le snapshot ne capture que l'état au moment où il tourne : il doit être exécuté à chaque chargement
  (orchestration Airflow), un changement intervenu puis annulé entre deux exécutions est perdu.
- Un relevé chargé plus de 24 heures en retard nécessite une reconstruction complète
  (`dbt build --full-refresh`).
