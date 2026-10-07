"""Client for the V'Lille GBFS feeds."""

import httpx

from vlille.models import StationInformationFeed, StationStatusFeed


class GbfsError(Exception):
    """The GBFS feed is not as expected (e.g. a feed missing from gbfs.json)."""


class GbfsClient:
    """Reads the feeds of a GBFS system from its `gbfs.json` entry point.

    The HTTP client is passed in, so tests can use a fake transport instead of the network.
    """

    def __init__(self, gbfs_url: str, http: httpx.Client) -> None:
        self._gbfs_url = gbfs_url
        self._http = http

    def feed_urls(self) -> dict[str, str]:
        """Return {feed name: URL}, read from gbfs.json."""
        languages = self._get_json(self._gbfs_url).get("data", {})
        if not languages:
            raise GbfsError(f"Aucune langue déclarée dans {self._gbfs_url}")
        # Every language lists the same feeds: take the first one.
        first_language = list(languages)[0]
        urls = {}
        for feed in languages[first_language]["feeds"]:
            urls[feed["name"]] = feed["url"]
        return urls

    def station_information(self) -> StationInformationFeed:
        return StationInformationFeed.model_validate_json(self.fetch_raw("station_information"))

    def station_status(self) -> StationStatusFeed:
        return StationStatusFeed.model_validate_json(self.fetch_raw("station_status"))

    def fetch_raw(self, name: str) -> bytes:
        """Download a feed and return the response as received, without validation."""
        urls = self.feed_urls()
        if name not in urls:
            raise GbfsError(f"Flux '{name}' absent de {self._gbfs_url}")
        return self._get(urls[name]).content

    def _get_json(self, url: str) -> dict:
        return self._get(url).json()

    def _get(self, url: str) -> httpx.Response:
        response = self._http.get(url)
        response.raise_for_status()
        return response
