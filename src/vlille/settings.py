"""Configuration read from environment variables (see .env.example)."""

import os


def env(name: str) -> str:
    """Return the variable, or stop the command with a clear message if it is missing."""
    value = os.environ.get(name)
    if not value:
        raise SystemExit(f"Variable d'environnement manquante : {name} (voir .env.example)")
    return value
