"""Client des flux GBFS V'Lille."""

import httpx

from vlille.models import StationInformationFeed, StationStatusFeed


class GbfsError(Exception):
    """Le flux GBFS ne correspond pas à ce qui est attendu (ex. flux absent de gbfs.json)."""


class GbfsClient:
    """Lit les flux d'un système GBFS à partir de son point d'entrée `gbfs.json`.

    Le client HTTP est fourni de l'extérieur : en production un `httpx.Client` réel (avec un
    timeout), en test un client branché sur un faux transport, sans appel réseau.
    """

    def __init__(self, gbfs_url: str, http: httpx.Client) -> None:
        self._gbfs_url = gbfs_url
        self._http = http

    def feed_urls(self) -> dict[str, str]:
        """Retourne {nom du flux: URL}, lu dans `gbfs.json`.

        - Lève `httpx.HTTPStatusError` si la réponse HTTP est une erreur.
        - Lève `GbfsError` si `gbfs.json` ne contient aucune langue.
        """
        languages = self._get_json(self._gbfs_url).get("data", {})
        if not languages:
            raise GbfsError(f"Aucune langue déclarée dans {self._gbfs_url}")
        feeds = next(iter(languages.values()))["feeds"]
        return {feed["name"]: feed["url"] for feed in feeds}

    def station_information(self) -> StationInformationFeed:
        """Télécharge et valide le flux `station_information`.

        Lève `GbfsError` si ce flux n'est pas déclaré dans `gbfs.json`.
        """
        return StationInformationFeed.model_validate_json(self.fetch_raw("station_information"))

    def station_status(self) -> StationStatusFeed:
        """Télécharge et valide le flux `station_status`.

        Lève `GbfsError` si ce flux n'est pas déclaré dans `gbfs.json`.
        """
        return StationStatusFeed.model_validate_json(self.fetch_raw("station_status"))

    def fetch_raw(self, name: str) -> bytes:
        """Télécharge un flux et retourne la réponse telle que reçue, sans validation.

        Lève `GbfsError` si ce flux n'est pas déclaré dans `gbfs.json`.
        """
        urls = self.feed_urls()
        if name not in urls:
            raise GbfsError(f"Flux {name!r} absent de {self._gbfs_url}")
        return self._get(urls[name]).content

    def _get_json(self, url: str) -> dict:
        return self._get(url).json()

    def _get(self, url: str) -> httpx.Response:
        response = self._http.get(url)
        response.raise_for_status()
        return response
