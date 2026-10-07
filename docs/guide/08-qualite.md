# 8. Qualité : tests et intégration continue

## Tests Python

[pytest](https://docs.pytest.org/), dans [`tests/`](../../tests/) : 35 tests, **sans réseau ni GCP**.

Chaque composant reçoit ses dépendances de l'extérieur (client HTTP, bucket, client BigQuery, producteur
ou consommateur Kafka) : en test, on lui passe une doublure en mémoire
([`tests/fakes.py`](../../tests/fakes.py)) et des extraits réels enregistrés
([`tests/fixtures/`](../../tests/fixtures/)). Exemples de comportements vérifiés :

- un flux invalide est archivé mais signalé ;
- deux collectes du même état ne créent qu'un fichier ;
- recharger un jour remplace sa partition ;
- le consommateur valide ses offsets après avoir écrit ses fichiers.

## Lint et formatage

[ruff](https://docs.astral.sh/ruff/) vérifie le code (erreurs, imports, syntaxe moderne) et son
formatage. Configuration dans [`pyproject.toml`](../../pyproject.toml).

## Tests de données dbt

33 tests exécutés par `dbt build` sur les vraies données (voir le [chapitre 5](05-dbt.md)) : un modèle
dont les données violent une règle fait échouer le build, donc la tâche Airflow.

## Intégration continue

[GitHub Actions](https://docs.github.com/actions), workflow
[`.github/workflows/ci.yml`](../../.github/workflows/ci.yml), à chaque pull request et à chaque push
sur `main` :

```
uv sync --locked  →  ruff check  →  ruff format --check  →  pytest
```

`--locked` fait échouer la CI si `uv.lock` ne correspond plus à `pyproject.toml`. Le jeton du workflow
est en lecture seule. La CI n'accède pas à GCP : les tests dbt tournent localement et sous Airflow.

## Façon de travailler

Chaque étape a été développée sur une branche, fusionnée par pull request après CI verte. Les choix
sont consignés dans des [ADR](../decisions/).

## Pour voir

Onglet **Actions** du dépôt GitHub : historique des exécutions de la CI.
