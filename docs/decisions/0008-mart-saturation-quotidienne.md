# 0008 — Mart de saturation quotidienne des stations

- Date : 2026-10-07
- Statut : accepté

## Contexte
Questions métier : quelles stations sont souvent vides ou pleines, et lesquelles demandent un
rééquilibrage. La capacité d'une station peut changer ; l'analyse doit utiliser celle valable au moment
de chaque remontée.

## Décision
- **`dim_station`** (table) : versions du snapshot `snap_station` avec une période
  `[valid_from, valid_to)` ; la première version est réputée valable depuis 1970, la version courante
  jusqu'en 9999.
- **`mart_station_daily`** (table recalculée entièrement) : une ligne par station et par jour (heure de
  Paris), à partir des remontées des stations installées, jointes à la version de la station valable
  à l'instant de la remontée.
- Indicateurs : nombre de remontées, part des remontées à 0 vélo (`share_empty`), à 0 place libre
  (`share_full`), nombre moyen de vélos, capacité.
- Besoin de rééquilibrage : « apporter des vélos » si `share_empty` ≥ seuil, sinon « retirer des vélos »
  si `share_full` ≥ seuil ; seuil en variable dbt `rebalancing_threshold` (0,2).

## Justification
- Première version valable depuis toujours : le snapshot a démarré après les premières remontées ;
  sans cette règle, la jointure perdrait les remontées antérieures (vérifié : 1 658 remontées en entrée,
  1 658 dans le mart).
- Table complète plutôt qu'incrémentale : volume faible, logique plus simple.
- Seuil en variable : règle métier modifiable sans toucher au SQL.

## Limites
- Les parts portent sur le nombre de remontées, pas sur la durée : les stations remontent à intervalles
  irréguliers et la collecte a des trous (poste éteint). Approximation assumée.
- Le seuil de 20 % est arbitraire.
- Avec peu de jours collectés, les résultats ne sont pas représentatifs.
