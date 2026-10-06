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
    routes = {GBFS_URL: gbfs} | {f"{BASE}{name}.json": body for name, body in feeds.items()}

    def handler(request: httpx.Request) -> httpx.Response:
        body = routes.get(str(request.url))
        return httpx.Response(200, json=body) if body else httpx.Response(404)

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

    status = next(data for name, data in bucket.objects.items() if "station_status" in name)
    archived = json.loads(gzip.decompress(status))
    assert archived["data"]["stations"][0]["num_bikes_available"] == -1
