# 0005 — Tables brutes BigQuery

- Date : 2026-10-06
- Statut : accepté, modifié par l'[ADR 0013](0013-kafka-source-des-disponibilites.md)

## Contexte
La zone brute GCS est purgée après 30 jours ; l'historique doit être conservé et interrogeable en SQL
pour la modélisation dbt. Le volume est faible (quelques Mo par jour).

## Décision
- Dataset `vlille_raw` (`europe-west1`, même région que le bucket), deux tables :
  `raw_station_information` et `raw_station_status`.
- Une ligne par fichier de la zone brute : `last_updated` (TIMESTAMP), `source_uri` (STRING),
  `payload` (JSON, réponse complète).
- Partition par jour sur `last_updated`, filtre de partition obligatoire.
- Chargement par jour (`vlille-load --date`) : load job qui remplace la partition du jour
  (`WRITE_TRUNCATE` sur `table$AAAAMMJJ`).

## Justification
- Chargement plutôt que table externe : les données survivent à la purge GCS et les load jobs sont
  gratuits.
- Réponse stockée en JSON sans découpage : la structure est interprétée par dbt (schema-on-read) ; un
  changement de format de la source ne casse pas le chargement.
- Remplacement de la partition : recharger un jour donne toujours le même résultat (idempotence), sans
  logique de dédoublonnage au chargement.
- Filtre de partition obligatoire : aucune requête ne peut lire toute la table par oubli.

## Alternatives écartées
- Table externe sur GCS : pas de copie, mais données perdues avec la purge à 30 jours.
- Découper les stations dès le chargement : transformation qui relève de dbt.
- Clustering : sans intérêt au volume du projet.

## Conséquences
- Le schéma est déclaré deux fois (`infra/raw_table_schema.json` pour la création, code du chargeur
  pour le load job) : à garder identiques.
- Un jour sans fichier laisse sa partition inchangée.
