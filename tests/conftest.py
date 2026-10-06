import json
from pathlib import Path

import pytest

FIXTURES = Path(__file__).parent / "fixtures"


@pytest.fixture
def load_fixture():
    """Charge un flux GBFS enregistré (extrait réel réduit à quelques stations)."""

    def _load(name: str) -> dict:
        return json.loads((FIXTURES / f"{name}.json").read_text(encoding="utf-8"))

    return _load
