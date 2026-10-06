# 0001 — Source de données : flux GBFS V'Lille

- Date : 2026-10-06
- Statut : accepté

## Contexte
Le projet a besoin de la disponibilité des stations V'Lille en quasi temps réel. Le jeu de données
« ilévia - V'Lille disponibilité en temps réel » (Métropole Européenne de Lille, Licence Ouverte 2.0,
référencé sur data.gouv.fr) propose deux types d'accès : des services OGC (WFS, OGC API Features) et
un flux GBFS publié par Ilévia.

## Décision
Utiliser le flux **GBFS 2.3** : `https://media.ilevia.fr/opendata/gbfs.json`, public et sans clé.
- `station_information` : référentiel des stations (268 stations le 2026-10-06) → dimension.
- `station_status` : disponibilité instantanée (environ une mise à jour par minute) → faits.

## Justification
- GBFS est un standard ouvert de la mobilité partagée, au schéma documenté : le code est réutilisable
  pour d'autres réseaux.
- Le flux sépare déjà référentiel et état, ce qui correspond à la modélisation visée.
- Les services OGC sont orientés cartographie.

## Alternatives écartées
- Services OGC de la MEL : orientés cartographie, format moins adapté à une collecte périodique.

## Conséquences
- `ttl` vaut 0 : la cadence de collecte est fixée par le projet.
- Une relecture peut renvoyer le même relevé : déduplication sur `(station_id, last_reported)`.
- Écarts observés le 2026-10-06, à traiter en qualité de données : une station présente dans
  `station_information` sans statut (id 1) ; des stations hors service (`is_installed` ou `is_renting`
  à faux).
- Service tiers sans engagement de disponibilité : la collecte doit tolérer erreurs et absences de
  réponse.
