# 0011 — Consommateur Kafka vers la zone brute GCS

- Date : 2026-10-07
- Statut : accepté

## Contexte
Les remontées publiées dans `vlille.station_status` doivent être conservées au-delà de la rétention
Kafka (7 jours), sans perte, et sans multiplier les écritures facturées dans GCS.

## Décision
- Commande **`vlille-consume`**, groupe de consommateurs `vlille-gcs-writer`, lecture depuis le début
  du topic au premier démarrage.
- Messages accumulés en **lots** (500 messages ou 300 secondes par défaut, paramétrables).
- Chaque lot est écrit dans le bucket de la zone brute, **un fichier par partition** :
  `kafka/station_status/dt=AAAA-MM-JJ/p<partition>-<premier offset>.ndjson.gz`, une ligne JSON par
  message, sans transformation.
- **Commit manuel des offsets, après l'écriture** (`enable.auto.commit` désactivé).

## Justification
- Écrire puis valider : un arrêt entre les deux fait relire et réécrire le lot au redémarrage, sans
  perte (garantie « au moins une fois »). L'ordre inverse perdrait les messages (« au plus une fois »).
- Les doublons possibles sont sans conséquence : la table de faits dédoublonne sur
  `(station_id, last_reported)`.
- Lots : quelques centaines d'écritures GCS par jour au lieu d'une par message.
- Nom de fichier : partition et premier offset identifient exactement le contenu.

## Alternatives écartées
- Commit automatique : les offsets peuvent être validés avant l'écriture, donc perte possible.
- « Exactement une fois » : demande des transactions Kafka et un stockage qui y participe ; hors de
  portée avec GCS.
- Écriture directe dans BigQuery (streaming) : coût et complexité supplémentaires.

## Conséquences
- Les fichiers du flux temps réel ne sont pas chargés dans BigQuery : hors du périmètre du projet,
  le chargement batch (`vlille-load`) reste la source des modèles dbt.
- Après un redémarrage, les noms de fichiers d'un lot rejoué peuvent différer (limites de lot
  différentes) : les doublons se retrouvent dans des fichiers distincts.
- Vérifié : 828 messages écrits en 7 fichiers, retard du groupe nul sur les 3 partitions.
