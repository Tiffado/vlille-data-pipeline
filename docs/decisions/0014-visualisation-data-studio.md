# 0014 — Visualisation avec Data Studio

- Date : 2026-10-07
- Statut : accepté

## Contexte
Les résultats n'étaient consultables qu'en SQL dans BigQuery. Il faut une couche de visualisation
gratuite, accessible par un simple lien et la plus simple possible.

## Décision
- Tableau de bord **Data Studio** (ex-Looker Studio, outil gratuit de Google), connecté directement à
  BigQuery sur la table `vlille_dev.mart_station_daily`.
- Page « Besoin de rééquilibrage » : carte des stations colorée selon la part du temps vide, tableau des
  stations triées par part du temps vide, sélecteur de période.
- Page « Etat actuel », sur la table `vlille_dev.mart_station_current` (une ligne par station) : carte
  des vélos disponibles à la dernière remontée chargée, heure de la remontée dans l'info-bulle.
- Partage public en lecture par lien ; la source utilise les identifiants du propriétaire : les
  visiteurs n'ont pas besoin de compte GCP.
- Le mart porte tout ce dont le tableau de bord a besoin : position (`location`, format
  « latitude,longitude »), besoin de rééquilibrage sans valeur vide (`aucun`), période de collecte
  seulement.
- Libellés lisibles définis dans Data Studio ; les colonnes de l'entrepôt gardent des noms techniques.

## Justification
- Gratuit, sans installation ni hébergement, connecteur BigQuery natif.
- Une seule table en entrée : pas de jointure dans l'outil de visualisation, la logique reste dans dbt.
- Le mart pèse quelques dizaines de Ko par jour : chaque affichage lit très peu de données.

## Alternatives écartées
- Metabase ou Superset en Docker : gratuits, mais limités au poste, pas accessibles par un lien.
- Streamlit : demande du code et un hébergement.

## Conséquences
- Le rapport est construit dans l'interface de Data Studio : il n'est pas versionné dans le dépôt.
- Les requêtes des visiteurs sont facturées au projet (volume négligeable).
- Les données affichées suivent le rafraîchissement de BigQuery (toutes les 3 heures).
