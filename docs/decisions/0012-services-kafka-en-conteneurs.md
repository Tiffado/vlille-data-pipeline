# 0012 — Producteur et consommateur Kafka en conteneurs

- Date : 2026-10-07
- Statut : accepté

## Contexte
Le producteur et le consommateur tournaient dans des terminaux : il fallait les relancer à la main
après chaque redémarrage du poste, et une mise à jour du projet était bloquée tant qu'ils tournaient.

## Décision
- Image du projet `kafka/Dockerfile` : `python:3.12-slim`, projet installé avec uv
  (`uv sync --locked --no-dev`), utilisateur sans droits d'administration.
- Services `producer` et `consumer` ajoutés à `kafka/docker-compose.yml`, `restart: always`,
  connexion au broker par le point d'entrée interne `kafka:19092`.
- Le consommateur reçoit le fichier ADC en lecture seule ; la configuration vient du `.env`.

## Justification
- Les services repartent avec Docker Desktop, comme Airflow, sans action manuelle.
- `restart: always` relance aussi un service qui s'arrête sur une erreur.
- Image séparée de celle d'Airflow : légère, sans dépendance à Airflow.

## Alternatives écartées
- Tâches Airflow : Airflow orchestre des traitements qui se terminent, pas des services continus.
- Planificateur Windows : ne redémarre pas un service arrêté et ne s'intègre pas à Docker.

## Conséquences
- Une modification du code demande de reconstruire l'image (`up -d --build`).
- Les journaux se lisent avec `docker compose ... logs`.
