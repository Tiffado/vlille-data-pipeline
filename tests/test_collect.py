import gzip
import json

import httpx
import pytest
from fakes import FakeBucket

from vlille.client import GbfsClient
from vlille.collect import collect
from vlille.raw_store import RawStore

GBFS_URL = "https://example.test/gbfs.json"
BASE = "https://media.ilevia.fr/opendata/"


def make_gbfs(feeds: dict[str, dict], gbfs: dict) -> GbfsClient:
    """Faux serveur : gbfs.json et chaque flux à son URL, 404 pour le reste."""
    routes = {GBFS_URL: gbfs}
    for name, body in feeds.items():
        routes[BASE + name + ".json"] = body

    def handler(request: httpx.Request) -> httpx.Response:
        url = str(request.url)
        if url not in routes:
            return httpx.Response(404)
        return httpx.Response(200, json=routes[url])

    return GbfsClient(GBFS_URL, httpx.Client(transport=httpx.MockTransport(handler)))


@pytest.fixture
def feeds(load_fixture) -> dict[str, dict]:
    return {
        "station_information": load_fixture("station_information"),
        "station_status": load_fixture("station_status"),
    }


def test_valid_feeds_are_archived(feeds, load_fixture):
    bucket = FakeBucket()

    assert collect(make_gbfs(feeds, load_fixture("gbfs")), RawStore(bucket)) is True
    assert sorted(name.split("/")[1] for name in bucket.objects) == [
        "station_information",
        "station_status",
    ]


def test_invalid_feed_is_archived_but_reported(feeds, load_fixture):
    feeds["station_status"]["data"]["stations"][0]["num_bikes_available"] = -1
    bucket = FakeBucket()

    assert collect(make_gbfs(feeds, load_fixture("gbfs")), RawStore(bucket)) is False

    status_files = [name for name in bucket.objects if "station_status" in name]
    assert len(status_files) == 1
    archived = json.loads(gzip.decompress(bucket.objects[status_files[0]]))
    assert archived["data"]["stations"][0]["num_bikes_available"] == -1
