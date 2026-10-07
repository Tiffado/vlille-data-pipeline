# 9. Visualisation avec Data Studio

## Le tableau de bord

**[Ouvrir le tableau de bord](https://datastudio.google.com/reporting/94e9208b-e444-4b38-a2eb-7d2ecd21763e)**
(public, sans compte)

- **Carte** des stations, colorée selon la part du temps où elles sont vides.
- **Tableau** des stations, triées de la plus souvent vide à la moins souvent vide, avec la part du
  temps pleine.
- **Sélecteur de période** : filtre la carte et le tableau.

## Data Studio en bref

[Data Studio](https://datastudio.google.com/) (anciennement Looker Studio) est l'outil gratuit de
tableaux de bord de Google : on y connecte une source (ici une table BigQuery), puis on compose des
graphiques par glisser-déposer. Un rapport se partage par lien, comme un document Google.

## Comment il est branché

- Source : une seule table, `vlille_dev.mart_station_daily`, une ligne par station et par jour.
  Toute la logique (jointure SCD2, agrégation, besoin de rééquilibrage) est dans dbt ; l'outil de
  visualisation ne fait qu'afficher.
- Le mart fournit la position au format attendu par la carte : colonne `location`,
  `latitude,longitude`, déclarée de type **Latitude, Longitude** dans la source.
- Les parts (`share_empty`, `share_full`) sont déclarées en **Pourcentage**, agrégation **Moyenne** :
  sur plusieurs jours, on affiche la moyenne des parts quotidiennes.
- Les noms de colonnes techniques sont renommés dans la source de données (« Station », « % vide »…) :
  l'entrepôt garde des noms stables, les libellés relèvent de la visualisation.
- Partage : lecture publique par lien, avec les identifiants du propriétaire. Les visiteurs n'ont pas
  besoin d'accès à GCP ; leurs requêtes, de quelques Ko, sont facturées au projet.

## Limites

- Le rapport est construit dans l'interface : il n'est pas versionné dans le dépôt.
- Les données suivent le rafraîchissement de BigQuery, toutes les 3 heures.
- Les parts sont calculées sur le nombre de remontées, approximation de la durée (voir le
  [chapitre 5](05-dbt.md)).

Décision : [ADR 0014](../decisions/0014-visualisation-data-studio.md).
