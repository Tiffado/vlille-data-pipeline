# 7. Temps réel avec Kafka

Cette partie existe pour apprendre Kafka : au volume du projet, la collecte batch suffirait.

## Kafka en bref

[Apache Kafka](https://kafka.apache.org/documentation/) est un journal de messages distribué. Des
**producteurs** écrivent des messages dans un **topic**, des **consommateurs** les lisent, chacun à son
rythme, sans se connaître. Les messages restent stockés pendant la durée de **rétention**, même lus.

| Notion | Sens | Dans le projet |
|---|---|---|
| Topic | Flux nommé | `vlille.station_status` |
| Partition | Journal ordonné ; un topic en a plusieurs, lues en parallèle | 3 |
| Clé | Choisit la partition : même clé, même partition, ordre conservé | `station_id` |
| Offset | Position d'un message dans sa partition | mémorisé par groupe de consommateurs |
| Groupe de consommateurs | Se partage les partitions, retient où il en est | `vlille-gcs-writer` |
| Réplication | Copies d'une partition sur plusieurs brokers | 1 (un seul broker) |

## Le broker local

[`kafka/docker-compose.yml`](../../kafka/docker-compose.yml) : Kafka 4.3, un seul nœud en mode
**KRaft** (il gère lui-même ses métadonnées, sans ZooKeeper). Deux points d'entrée :
`kafka:19092` pour les autres conteneurs, `localhost:9092` pour le poste, car un client se reconnecte
toujours à l'adresse que le broker lui annonce. Le topic est créé au démarrage, rétention 7 jours.

Client Python : [confluent-kafka](https://docs.confluent.io/kafka-clients/python/current/overview.html).

## Le producteur : `vlille-produce`

[`produce.py`](../../src/vlille/produce.py) interroge `station_status` toutes les 60 secondes et publie
**un message par station dont `last_reported` a changé** : un message correspond à un événement réel.
Clé `station_id`, valeur JSON, `acks=all` (confirmation une fois le message écrit par les répliques).
Il tourne en continu, dans un terminal.

## Le consommateur : `vlille-consume`

[`consume.py`](../../src/vlille/consume.py) lit le topic, accumule les messages en lots (500 messages
ou 5 minutes) et écrit un fichier par partition dans la zone brute :

```
kafka/station_status/dt=2026-10-07/p1-000000000267.ndjson.gz
```

Une ligne JSON par message, sans transformation. Les offsets sont validés **après** l'écriture : en cas
d'arrêt brutal, le lot non validé est relu et réécrit au redémarrage. Garantie **au moins une fois** :
aucune perte, doublons possibles (éliminés en aval sur `(station_id, last_reported)`).

Ces fichiers ne sont pas chargés dans BigQuery : hors du périmètre du projet.

## Lancer et voir

```bash
docker compose -f kafka/docker-compose.yml up -d
uv run --env-file .env vlille-produce     # terminal 1
uv run --env-file .env vlille-consume     # terminal 2
```

Retard du consommateur (`LAG` = messages en attente) :

```bash
docker compose -f kafka/docker-compose.yml exec kafka /opt/kafka/bin/kafka-consumer-groups.sh --bootstrap-server localhost:9092 --describe --group vlille-gcs-writer
```

Fichiers écrits : dossier `kafka/` du bucket dans la
[console Cloud Storage](https://console.cloud.google.com/storage/browser/vlille-pipeline-raw?project=vlille-pipeline).

Décisions : [ADR 0010](../decisions/0010-kafka-producteur.md),
[ADR 0011](../decisions/0011-kafka-consommateur.md).
