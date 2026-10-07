# 3. Collecte et zone brute

## Ce que fait `vlille-collect`

Pour le référentiel des stations (`station_information`) : télécharger la réponse, l'**archiver telle
quelle** dans Cloud Storage, puis la **valider**. Les disponibilités (`station_status`) n'arrivent pas
par ici mais par Kafka ([chapitre 7](07-kafka.md)). Si un flux est invalide, il est quand même archivé (preuve de ce qui a été reçu)
et la commande se termine en erreur (code de retour 1), pour qu'un orchestrateur le signale.

```
gbfs.json ──► URL de chaque flux ──► réponse brute ──► GCS (gzip) ──► validation pydantic
```

## Les modules

| Module | Rôle |
|---|---|
| [`client.py`](../../src/vlille/client.py) | `GbfsClient` : lit `gbfs.json`, trouve l'URL d'un flux, le télécharge (`fetch_raw`) ou le télécharge et le valide |
| [`models.py`](../../src/vlille/models.py) | Modèles pydantic des flux : champs typés et bornés (`num_bikes_available >= 0`…), horodatages convertis en UTC, champs inconnus ignorés |
| [`raw_store.py`](../../src/vlille/raw_store.py) | `RawStore` : nomme et écrit les réponses dans le bucket |
| [`paths.py`](../../src/vlille/paths.py) | Organisation de la zone brute : préfixes `gbfs/` (batch) et `kafka/station_status/` (Kafka) |
| [`collect.py`](../../src/vlille/collect.py) | La commande : enchaîne collecte, archivage, validation |

## Bibliothèques

- [**httpx**](https://www.python-httpx.org/) : client HTTP. Le client est créé par l'appelant et
  *injecté* dans `GbfsClient` : en test, on lui passe un faux serveur (`httpx.MockTransport`), sans
  réseau.
- [**pydantic**](https://docs.pydantic.dev/) : validation par modèles typés. Une donnée qui ne respecte
  pas le contrat (champ manquant, nombre négatif) lève une erreur précise dès la collecte, au lieu
  d'apparaître plus tard dans BigQuery.
- [**google-cloud-storage**](https://cloud.google.com/python/docs/reference/storage/latest) : écriture
  dans le bucket.

## La zone brute dans Cloud Storage

Un **bucket** est un conteneur d'objets dans Cloud Storage, adressé par `gs://nom/...`. Il n'y a pas
de vrais dossiers : le « chemin » fait partie du nom de l'objet. Contrairement à HDFS, le stockage est
séparé du calcul : on paie au volume et aux opérations, sans cluster.

Bucket `gs://vlille-pipeline-raw`, organisé par source et par jour à la manière de Hive :

```
gbfs/station_information/dt=2026-10-07/station_information_20261007T095301Z.json.gz   (batch)
kafka/station_status/dt=2026-10-07/p1-000000000267.ndjson.gz                          (Kafka)
```

- **Nom tiré de `last_updated` du flux**, pas de l'heure de collecte : deux collectes du même état
  écrivent le même objet, la seconde remplaçant la première par un contenu identique. Pas de doublon :
  c'est l'**idempotence**.
- **Compression gzip** : environ 100 Ko de JSON deviennent 3 Ko.
- **Sécurité** : accès uniforme au niveau du bucket (droits IAM uniquement), accès public bloqué.
- **Cycle de vie** : suppression automatique après 30 jours ([`infra/gcs-lifecycle.json`](../../infra/gcs-lifecycle.json)).
  Les données restent dans BigQuery.

## Lancer à la main

```bash
uv run --env-file .env vlille-collect
```

## Pour voir

- Le bucket dans la console :
  <https://console.cloud.google.com/storage/browser/vlille-pipeline-raw?project=vlille-pipeline>
  (onglets « Cycle de vie » et « Autorisations » pour les règles).

Décision : [ADR 0004](../decisions/0004-zone-brute-gcs.md).
