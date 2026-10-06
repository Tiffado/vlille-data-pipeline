"""Lecture de la configuration (variables d'environnement, voir .env.example)."""

import os


def env(name: str) -> str:
    """Retourne la variable demandée ; arrête la commande avec un message clair si elle manque."""
    value = os.environ.get(name)
    if not value:
        raise SystemExit(f"Variable d'environnement manquante : {name} (voir .env.example)")
    return value
