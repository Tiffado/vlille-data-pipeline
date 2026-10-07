# Lancer le projet

Procédure pour un poste Windows avec PowerShell. Les commandes se lancent depuis la racine du dépôt.

- [Après un redémarrage du PC](#après-un-redémarrage-du-pc) : la procédure courante
- [Première installation](#première-installation)
- [Toutes les commandes](#toutes-les-commandes)
- [Arrêter](#arrêter)
- [Dépannage](#dépannage)

## Après un redémarrage du PC

### 1. Démarrer Docker Desktop

Lancer **Docker Desktop** (menu Démarrer) et attendre « Engine running ». Pour qu'il démarre seul :
Settings → General → *Start Docker Desktop when you sign in to your computer*.

```bash
docker info --format "{{.ServerVersion}}"
```

Une version s'affiche : le moteur tourne.

### 2. Vérifier qu'Airflow et Kafka sont repartis

Les conteneurs sont configurés pour redémarrer avec Docker (`restart: always`).

```bash
docker compose -f airflow/docker-compose.yml ps
docker compose -f kafka/docker-compose.yml ps
```

Attendu : `postgres`, `airflow-apiserver`, `airflow-scheduler`, `airflow-dag-processor`, `kafka`,
`producer` et `consumer` en `running` (`airflow-init` et `kafka-init` sont normalement arrêtés). Sinon :

```bash
docker compose -f airflow/docker-compose.yml up -d
docker compose -f kafka/docker-compose.yml up -d
```

### 3. Vérifier les identifiants Google Cloud

```bash
gcloud auth application-default print-access-token
```

Un long jeton s'affiche : tout va bien. En cas d'erreur (`invalid_grant`, `reauth`…) :

```bash
gcloud auth application-default login
```

Puis redémarrer Airflow et le consommateur Kafka pour qu'ils relisent le fichier :
`docker compose -f airflow/docker-compose.yml restart` et
`docker compose -f kafka/docker-compose.yml restart consumer`.

### 4. Contrôler Airflow

Ouvrir <http://localhost:8081>, DAG **vlille_pipeline** : il doit être actif (interrupteur allumé) et un
run doit apparaître dans les 3 heures. **Trigger** lance un run immédiatement.

### 5. Contrôler le temps réel

Le producteur et le consommateur tournent dans des conteneurs et repartent seuls avec Docker. Leur
activité :

```bash
docker compose -f kafka/docker-compose.yml logs --tail 5 producer consumer
```

Le producteur écrit une ligne par minute, le consommateur une ligne par lot (toutes les 5 minutes).

## Première installation

1. **Outils** :

   ```bash
   powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
   ```

   ```bash
   winget install -e --id Google.CloudSDK
   ```

   ```bash
   wsl --install --no-distribution
   ```

   (redémarrer le PC), puis :

   ```bash
   winget install -e --id Docker.DockerDesktop
   ```

   Si PowerShell refuse d'exécuter `gcloud` : `Set-ExecutionPolicy -Scope CurrentUser RemoteSigned`.

2. **Projet Python** :

   ```bash
   uv sync
   Copy-Item .env.example .env
   ```

   Adapter `.env` si le projet GCP ou le bucket portent d'autres noms.

3. **Google Cloud** : projet rattaché à la facturation, budget avec alertes, API activées :

   ```bash
   gcloud init
   gcloud auth application-default login
   gcloud auth application-default set-quota-project vlille-pipeline
   gcloud services enable bigquery.googleapis.com storage.googleapis.com billingbudgets.googleapis.com
   ```

   Créer le bucket et les tables : commandes dans [`infra/README.md`](../infra/README.md).

4. **Vérifier** :

   ```bash
   uv run pytest
   uv run --env-file .env vlille-collect
   uv run --env-file .env dbt debug --project-dir dbt --profiles-dir dbt
   ```

5. **Démarrer Airflow et Kafka** (avec le producteur et le consommateur) :

   ```bash
   docker compose -f airflow/docker-compose.yml up -d --build
   docker compose -f kafka/docker-compose.yml up -d --build
   ```

   Dans <http://localhost:8081>, activer le DAG `vlille_pipeline` (il est en pause à sa création).

## Toutes les commandes

| Besoin | Commande |
|---|---|
| Installer / mettre à jour l'environnement | `uv sync` |
| Tests Python | `uv run pytest` |
| Lint et formatage | `uv run ruff check` et `uv run ruff format` |
| Collecter une fois | `uv run --env-file .env vlille-collect` |
| Charger des jours dans BigQuery | `uv run --env-file .env vlille-load --date 2026-10-06 2026-10-07` |
| Construire et tester les modèles dbt | `uv run --env-file .env dbt build --project-dir dbt --profiles-dir dbt` |
| Reconstruire tout l'incrémental dbt | ajouter `--full-refresh` à la commande précédente |
| Générer la documentation dbt | `uv run --env-file .env dbt docs generate --project-dir dbt --profiles-dir dbt` |
| Servir la documentation dbt (<http://localhost:8080>) | `uv run --env-file .env dbt docs serve --project-dir dbt --profiles-dir dbt` |
| Démarrer Airflow (et reconstruire l'image après une modification du code ou de dbt) | `docker compose -f airflow/docker-compose.yml up -d --build` |
| Interface Airflow | <http://localhost:8081> |
| Démarrer Kafka, le producteur et le consommateur (et reconstruire leur image après une modification du code) | `docker compose -f kafka/docker-compose.yml up -d --build` |
| Journaux du producteur et du consommateur | `docker compose -f kafka/docker-compose.yml logs -f producer consumer` |
| Producteur ou consommateur à la main, hors Docker (pour déboguer ; arrêter d'abord le conteneur correspondant) | `uv run --env-file .env vlille-produce` / `vlille-consume` |
| Retard du consommateur | `docker compose -f kafka/docker-compose.yml exec kafka /opt/kafka/bin/kafka-consumer-groups.sh --bootstrap-server localhost:9092 --describe --group vlille-gcs-writer` |
| Lire quelques messages du topic | `docker compose -f kafka/docker-compose.yml exec kafka /opt/kafka/bin/kafka-console-consumer.sh --bootstrap-server localhost:9092 --topic vlille.station_status --from-beginning --max-messages 5` |
| État des conteneurs | `docker compose -f airflow/docker-compose.yml ps` (idem avec `kafka/`) |
| Journaux d'un service | `docker compose -f airflow/docker-compose.yml logs -f airflow-scheduler` |

Consoles GCP : [Cloud Storage](https://console.cloud.google.com/storage/browser/vlille-pipeline-raw?project=vlille-pipeline),
[BigQuery](https://console.cloud.google.com/bigquery?project=vlille-pipeline),
[facturation](https://console.cloud.google.com/billing/reports?project=vlille-pipeline).

## Arrêter

- Documentation dbt, ou commande lancée à la main : `Ctrl+C` dans son terminal.
- Producteur et consommateur seuls : `docker compose -f kafka/docker-compose.yml stop producer consumer`.
- Airflow et Kafka (les données sont conservées dans des volumes Docker) :

  ```bash
  docker compose -f airflow/docker-compose.yml down
  docker compose -f kafka/docker-compose.yml down
  ```

  Ajouter `-v` supprime aussi les volumes : historique Airflow et messages Kafka **définitivement
  effacés**.

## Dépannage

| Symptôme | Cause probable | Solution |
|---|---|---|
| `uv`, `gcloud` ou `docker` « n'est pas reconnu » | Terminal ouvert avant l'installation | Ouvrir un nouveau terminal (ou redémarrer l'application qui l'héberge) |
| `failed to connect to the docker API` | Docker Desktop n'est pas lancé | Lancer Docker Desktop, attendre « Engine running » |
| Une autre application s'affiche sur un port | Port déjà occupé (8080 : dbt docs, 8081 : Airflow) | Arrêter le programme qui l'occupe ; vider le cache du navigateur (`Ctrl+F5`) |
| Tâche Airflow en échec | Voir son journal | Interface Airflow → run → tâche → **Logs** |
| `invalid_grant` ou `Reauthentication` | Identifiants GCP expirés | `gcloud auth application-default login`, puis redémarrer Airflow |
| `Cannot query over table ... without a filter over column(s) 'last_updated'` | Filtre de partition obligatoire | Ajouter `WHERE DATE(last_updated) = ...` à la requête |
| Producteur : `Connection refused` sur `localhost:9092` | Kafka arrêté | `docker compose -f kafka/docker-compose.yml up -d` |
| `uv sync` : fichier `.exe` « utilisé par un autre processus » | Une commande du projet tourne encore | Arrêter le producteur ou le consommateur (`Ctrl+C`), relancer `uv sync` |
| Modification du code sans effet dans Airflow, le producteur ou le consommateur | Image non reconstruite | `docker compose -f airflow/docker-compose.yml up -d --build` (idem avec `kafka/`) |
