import httpx
import pytest

from vlille.client import GbfsClient, GbfsError

GBFS_URL = "https://example.test/gbfs.json"
BASE = "https://media.ilevia.fr/opendata/"


def make_client(routes: dict[str, httpx.Response]) -> GbfsClient:
    """Client branché sur un faux transport : chaque URL renvoie la réponse prévue, sinon 404."""

    def handler(request: httpx.Request) -> httpx.Response:
        return routes.get(str(request.url), httpx.Response(404))

    return GbfsClient(GBFS_URL, httpx.Client(transport=httpx.MockTransport(handler)))


@pytest.fixture
def routes(load_fixture) -> dict[str, httpx.Response]:
    return {
        GBFS_URL: httpx.Response(200, json=load_fixture("gbfs")),
        BASE + "station_information.json": httpx.Response(
            200, json=load_fixture("station_information")
        ),
        BASE + "station_status.json": httpx.Response(200, json=load_fixture("station_status")),
    }


def test_feed_urls_lists_declared_feeds(routes):
    urls = make_client(routes).feed_urls()

    assert urls["station_status"] == BASE + "station_status.json"
    assert urls["station_information"] == BASE + "station_information.json"


def test_station_information_is_fetched_and_validated(routes):
    feed = make_client(routes).station_information()

    assert [s.station_id for s in feed.data.stations] == ["1", "2", "3"]


def test_station_status_is_fetched_and_validated(routes):
    feed = make_client(routes).station_status()

    assert [s.station_id for s in feed.data.stations] == ["2", "3"]


def test_fetch_raw_returns_bytes_as_received(routes):
    raw = make_client(routes).fetch_raw("station_status")

    assert raw == routes[BASE + "station_status.json"].content


def test_http_error_is_raised(routes):
    routes[GBFS_URL] = httpx.Response(503)

    with pytest.raises(httpx.HTTPStatusError):
        make_client(routes).feed_urls()


def test_missing_feed_raises_gbfs_error(routes, load_fixture):
    gbfs = load_fixture("gbfs")
    gbfs["data"]["en"]["feeds"] = [
        f for f in gbfs["data"]["en"]["feeds"] if f["name"] != "station_status"
    ]
    routes[GBFS_URL] = httpx.Response(200, json=gbfs)

    with pytest.raises(GbfsError):
        make_client(routes).station_status()


def test_gbfs_without_language_raises_gbfs_error(routes):
    routes[GBFS_URL] = httpx.Response(200, json={"ttl": 0, "version": "2.3", "data": {}})

    with pytest.raises(GbfsError):
        make_client(routes).feed_urls()
