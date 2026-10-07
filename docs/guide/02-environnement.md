# 2. Environnement de travail

## Outils installés sur le poste

| Outil | Rôle | Lien |
|---|---|---|
| **uv** | Gestionnaire Python : installe Python 3.12, crée l'environnement virtuel, verrouille les dépendances | [docs.astral.sh/uv](https://docs.astral.sh/uv/) |
| **Docker Desktop** | Fait tourner les conteneurs (Airflow, Kafka) ; sous Windows, s'appuie sur WSL2 | [docs.docker.com](https://docs.docker.com/desktop/) |
| **CLI Google Cloud** (`gcloud`, `bq`) | Pilote GCP depuis le terminal et fournit les identifiants locaux | [cloud.google.com/sdk](https://cloud.google.com/sdk/docs) |
| **git** et **gh** | Versionnement, pull requests | [cli.github.com](https://cli.github.com/) |

## Le projet Python

Le code est un paquet installable, `vlille`, décrit par [`pyproject.toml`](../../pyproject.toml) :

- **dépendances** : ce dont le code a besoin pour tourner (httpx, pydantic, bibliothèques Google,
  dbt-bigquery, confluent-kafka) ;
- **groupe `dev`** : outils de développement seulement (pytest, ruff) ;
- **`[project.scripts]`** : les commandes `vlille-collect`, `vlille-load`, `vlille-produce`,
  `vlille-consume`, disponibles après installation.

`uv.lock` fige la version exacte de chaque dépendance, y compris indirecte : la même installation sur
le poste, en CI et dans l'image Docker d'Airflow. `.python-version` fixe Python 3.12.

Le code est rangé en *layout* `src/` (`src/vlille/`) : les tests importent le paquet installé, pas les
fichiers du dossier courant, ce qui révèle immédiatement une erreur de packaging.

```bash
uv sync          # crée .venv et installe tout
uv run pytest    # lance une commande dans l'environnement du projet
```

## Configuration

Toute la configuration passe par des variables d'environnement, lues dans un fichier `.env` local
(jamais versionné). [`.env.example`](../../.env.example) documente les variables attendues :

| Variable | Exemple | Usage |
|---|---|---|
| `VLILLE_GBFS_URL` | `https://media.ilevia.fr/opendata/gbfs.json` | Source |
| `GOOGLE_CLOUD_PROJECT` | `vlille-pipeline` | Projet GCP (nom standard lu par les bibliothèques Google) |
| `GCS_RAW_BUCKET` | `vlille-pipeline-raw` | Bucket de la zone brute |
| `BQ_DATASET_RAW` | `vlille_raw` | Dataset des tables brutes |
| `KAFKA_BOOTSTRAP_SERVERS` | `localhost:9092` | Adresse du broker Kafka |

## Google Cloud

- Un projet GCP dédié, rattaché à un compte de facturation : BigQuery en mode gratuit (*sandbox*)
  interdit les `MERGE` dont dbt a besoin.
- Un **budget** de 5 € par mois avec alertes à 50, 90, 100 % du coût réel et 100 % du coût prévisionnel.
  Une alerte prévient, elle ne coupe rien.
- Seules les API utilisées sont activées : BigQuery, Cloud Storage, Billing Budget.
- Région unique `europe-west1` pour tout.

### Authentification sans clé

`gcloud auth application-default login` crée des **Application Default Credentials** (ADC) : un jeton
local que les bibliothèques Python, dbt et les conteneurs Airflow utilisent automatiquement. Aucune clé
de compte de service n'est téléchargée, donc aucun secret ne peut être commité par erreur.

### Coût observé

Quelques centimes par mois : stockage de quelques Mo par jour, chargements BigQuery gratuits, requêtes
dans le quota gratuit. Le poste le plus coûteux est le nombre d'écritures dans Cloud Storage.

## Pour voir

- Console GCP du projet : <https://console.cloud.google.com/home/dashboard?project=vlille-pipeline>
- Rapports de facturation : <https://console.cloud.google.com/billing/reports?project=vlille-pipeline>

Décisions : [ADR 0002](../decisions/0002-outillage-python.md) (outillage Python),
[ADR 0003](../decisions/0003-gcp-region-auth-couts.md) (GCP).
