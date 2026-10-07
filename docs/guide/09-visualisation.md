# 9. Visualisation avec Data Studio

## Le tableau de bord

**[Ouvrir le tableau de bord](https://datastudio.google.com/reporting/94e9208b-e444-4b38-a2eb-7d2ecd21763e)**
(public, sans compte)

Deux pages :

- **Besoin de rééquilibrage** (table `mart_station_daily`) :
  - carte des stations, colorée selon la part du temps où elles sont vides ;
  - tableau des stations, triées de la plus souvent vide à la moins souvent vide, avec la part du
    temps pleine ;
  - sélecteur de période, qui filtre la carte et le tableau.
- **Etat actuel** (table `mart_station_current`) : carte des stations, taille et couleur des bulles
  selon le nombre de vélos disponibles à la dernière remontée ; l'info-bulle donne le nom de la station
  et l'heure de cette remontée.

« Actuel » signifie : dernière remontée chargée dans BigQuery, donc vieille de 3 h 30 au plus (lots de
30 minutes du consommateur Kafka, puis chargement et dbt toutes les 3 heures). Le bouton **Trigger**
du DAG dans Airflow rafraîchit immédiatement.

## Data Studio en bref

[Data Studio](https://datastudio.google.com/) (anciennement Looker Studio) est l'outil gratuit de
tableaux de bord de Google : on y connecte une source (ici une table BigQuery), puis on compose des
graphiques par glisser-déposer. Un rapport se partage par lien, comme un document Google.

## Comment il est branché

- Sources : une table par page, `vlille_dev.mart_station_daily` (une ligne par station et par jour) et
  `vlille_dev.mart_station_current` (une ligne par station). Toute la logique (jointure SCD2,
  agrégation, dernière remontée, besoin de rééquilibrage, libellés) est dans dbt ; l'outil de
  visualisation ne fait qu'afficher.
- L'info-bulle d'une carte n'affiche qu'un champ texte : `mart_station_current` fournit
  `station_label`, qui réunit le nom de la station et l'heure de sa remontée.
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
