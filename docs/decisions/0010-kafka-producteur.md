# 0010 — Kafka local et producteur des remontées de stations

- Date : 2026-10-07
- Statut : accepté

## Contexte
La collecte batch photographie l'API toutes les 30 minutes. L'objectif de la phase 3 est d'apprendre
Kafka en publiant les remontées des stations au fil de l'eau. Le volume ne le justifie pas : c'est un
choix d'apprentissage assumé.

## Décision
- **Kafka 4.3** en local (`kafka/docker-compose.yml`) : un seul nœud en mode KRaft (broker et
  contrôleur, sans ZooKeeper), deux points d'entrée : `kafka:19092` pour les conteneurs,
  `localhost:9092` pour le poste.
- Topic **`vlille.station_status`** : 3 partitions, facteur de réplication 1, rétention 7 jours, créé
  au démarrage ; création automatique de topics désactivée.
- Commande **`vlille-produce`** (client `confluent-kafka`) : interroge `station_status` toutes les
  60 secondes et publie **un message par station dont `last_reported` a changé**, clé `station_id`,
  valeur JSON (état de la station + horodatage du relevé), `acks=all`.

## Justification
- Clé `station_id` : tous les messages d'une station vont dans la même partition, leur ordre est
  conservé.
- Publier les changements plutôt que l'état complet : un message correspond à un événement réel.
- Mémoire des dernières remontées en local : simple ; après un redémarrage, toutes les stations sont
  republiées une fois, ce que le consommateur doit tolérer (doublons possibles).
- Points d'entrée séparés : l'adresse annoncée par le broker doit être joignable depuis le client.

## Alternatives écartées
- Kafka managé (Confluent Cloud, Managed Kafka de GCP) : payant, hors du cadre local.
- Publier l'état complet à chaque passage : beaucoup de messages sans information nouvelle.

## Conséquences
- Un seul broker, sans réplication : aucune tolérance à la panne du broker (limite locale assumée).
- Le producteur est un processus qui tourne en continu dans un terminal ; il ne tourne pas sous
  Airflow, qui orchestre des traitements par lots.
- Vérifié : 267 messages au premier passage, puis environ 70 par minute, répartis sur les 3 partitions.
