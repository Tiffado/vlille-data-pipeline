# 0002 — Outillage Python : uv, layout `src/`, pytest, ruff

- Date : 2026-10-06
- Statut : accepté

## Contexte
Le code Python (collecte, chargement, plus tard producteur et consommateur Kafka) doit s'installer de
la même façon en local, en CI et dans une image Docker.

## Décision
- **uv** pour installer Python, créer l'environnement et verrouiller les dépendances (`uv.lock` et
  `.python-version` versionnés). Python 3.12.
- Paquet installable `vlille` en layout `src/`, décrit par `pyproject.toml` (backend hatchling).
- Dépendances de développement (pytest, ruff) dans un groupe séparé.
- **pytest** pour les tests, **ruff** pour le lint et le formatage.

## Justification
- Le fichier de verrouillage rend les installations reproductibles, dépendances indirectes comprises.
- Le layout `src/` oblige les tests à importer le paquet installé : une erreur de packaging se voit
  immédiatement.
- ruff regroupe lint, tri des imports et formatage en un seul outil rapide.

## Alternatives écartées
- pip + venv : pas de verrouillage natif.
- Poetry : fonctionnellement équivalent ; uv retenu pour sa rapidité (utile en CI) et la gestion
  intégrée des versions de Python.

## Conséquences
- Toute commande passe par `uv run` (ex. `uv run pytest`).
- Un ajout de dépendance se fait par `uv add`, qui met à jour `pyproject.toml` et `uv.lock`.
