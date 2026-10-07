# Liens utiles

Tous les accès du projet en un seul endroit. Les interfaces locales ne répondent que si les services
tournent sur le poste (voir [RUN.md](RUN.md)).

## Interfaces locales

| Interface | Adresse | Condition |
|---|---|---|
| Airflow | <http://localhost:8081> | Docker Desktop lancé (démarre avec lui) |
| Documentation dbt | <http://localhost:8080> | après `uv run --env-file .env dbt docs serve --project-dir dbt --profiles-dir dbt` |

Kafka n'a pas d'interface web : son état se consulte en ligne de commande (lag du consommateur, lecture
du topic, journaux des conteneurs), commandes dans [RUN.md](RUN.md#toutes-les-commandes). Les journaux
des conteneurs sont aussi visibles dans Docker Desktop, onglet **Containers**.

## Google Cloud (projet `vlille-pipeline`)

### Données

| Ressource | Lien |
|---|---|
| Zone brute (bucket) | <https://console.cloud.google.com/storage/browser/vlille-pipeline-raw?project=vlille-pipeline> |
| Zone brute : référentiel (batch) | <https://console.cloud.google.com/storage/browser/vlille-pipeline-raw/gbfs/station_information?project=vlille-pipeline> |
| Zone brute : messages Kafka | <https://console.cloud.google.com/storage/browser/vlille-pipeline-raw/kafka/station_status?project=vlille-pipeline> |
| BigQuery Studio | <https://console.cloud.google.com/bigquery?project=vlille-pipeline> |
| Table `vlille_raw.raw_station_information` | <https://console.cloud.google.com/bigquery?project=vlille-pipeline&p=vlille-pipeline&d=vlille_raw&t=raw_station_information&page=table> |
| Table `vlille_raw.raw_station_status_stream` | <https://console.cloud.google.com/bigquery?project=vlille-pipeline&p=vlille-pipeline&d=vlille_raw&t=raw_station_status_stream&page=table> |
| Table `vlille_dev.fct_station_status` | <https://console.cloud.google.com/bigquery?project=vlille-pipeline&p=vlille-pipeline&d=vlille_dev&t=fct_station_status&page=table> |
| Table `vlille_dev.mart_station_daily` | <https://console.cloud.google.com/bigquery?project=vlille-pipeline&p=vlille-pipeline&d=vlille_dev&t=mart_station_daily&page=table> |
| Snapshot `vlille_dev.snap_station` | <https://console.cloud.google.com/bigquery?project=vlille-pipeline&p=vlille-pipeline&d=vlille_dev&t=snap_station&page=table> |

Dans BigQuery, l'onglet **Aperçu** d'une table est gratuit ; une requête est facturée au volume lu,
affiché avant l'exécution.

### Coûts et administration

| Ressource | Lien |
|---|---|
| Tableau de bord du projet | <https://console.cloud.google.com/home/dashboard?project=vlille-pipeline> |
| Rapports de facturation | <https://console.cloud.google.com/billing/reports?project=vlille-pipeline> |
| Budgets et alertes | <https://console.cloud.google.com/billing/budgets?project=vlille-pipeline> |
| Journaux (audit, requêtes BigQuery) | <https://console.cloud.google.com/logs/query?project=vlille-pipeline> |
| Droits IAM | <https://console.cloud.google.com/iam-admin/iam?project=vlille-pipeline> |
| API activées | <https://console.cloud.google.com/apis/dashboard?project=vlille-pipeline> |

## GitHub

| Ressource | Lien |
|---|---|
| Dépôt | <https://github.com/Tiffado/vlille-data-pipeline> |
| Intégration continue (Actions) | <https://github.com/Tiffado/vlille-data-pipeline/actions> |
| Pull requests | <https://github.com/Tiffado/vlille-data-pipeline/pulls?q=is%3Apr> |

## Source de données

| Ressource | Lien |
|---|---|
| Point d'entrée GBFS V'Lille | <https://media.ilevia.fr/opendata/gbfs.json> |
| Flux des disponibilités | <https://media.ilevia.fr/opendata/station_status.json> |
| Flux du référentiel | <https://media.ilevia.fr/opendata/station_information.json> |
| Jeu de données sur data.gouv.fr | <https://www.data.gouv.fr/datasets/vlille-disponibilite-en-temps-reel-3> |
| Spécification GBFS | <https://gbfs.org/> |

## Documentation des outils

| Outil | Documentation |
|---|---|
| uv | <https://docs.astral.sh/uv/> |
| httpx | <https://www.python-httpx.org/> |
| pydantic | <https://docs.pydantic.dev/> |
| Cloud Storage (bibliothèque Python) | <https://cloud.google.com/python/docs/reference/storage/latest> |
| BigQuery | <https://cloud.google.com/bigquery/docs> |
| BigQuery (bibliothèque Python) | <https://cloud.google.com/python/docs/reference/bigquery/latest> |
| dbt | <https://docs.getdbt.com/> |
| Apache Airflow | <https://airflow.apache.org/docs/> |
| Apache Kafka | <https://kafka.apache.org/documentation/> |
| confluent-kafka (client Python) | <https://docs.confluent.io/kafka-clients/python/current/overview.html> |
| Docker | <https://docs.docker.com/> |
| pytest | <https://docs.pytest.org/> |
| ruff | <https://docs.astral.sh/ruff/> |
| GitHub Actions | <https://docs.github.com/actions> |
