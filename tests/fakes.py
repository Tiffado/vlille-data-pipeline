"""Doublures de test partagées."""


class FakeBlob:
    def __init__(self, bucket: "FakeBucket", name: str) -> None:
        self._bucket = bucket
        self.name = name

    def upload_from_string(self, data, content_type):
        self._bucket.objects[self.name] = data
        self._bucket.content_types[self.name] = content_type

    def download_as_bytes(self) -> bytes:
        return self._bucket.objects[self.name]


class FakeBucket:
    """Bucket en mémoire : reproduit seulement ce que le projet utilise."""

    name = "bucket-de-test"

    def __init__(self) -> None:
        self.objects: dict[str, bytes] = {}
        self.content_types: dict[str, str] = {}

    def blob(self, name: str) -> FakeBlob:
        return FakeBlob(self, name)

    def list_blobs(self, prefix: str) -> list[FakeBlob]:
        return [FakeBlob(self, name) for name in sorted(self.objects) if name.startswith(prefix)]


class FakeLoadJob:
    def result(self) -> None:
        return None


class FakeBigQuery:
    """Client BigQuery qui enregistre les chargements demandés au lieu de les exécuter."""

    def __init__(self) -> None:
        self.loads: list[tuple[str, list[dict], object]] = []

    def load_table_from_json(self, rows, table, job_config):
        self.loads.append((table, rows, job_config))
        return FakeLoadJob()


class FakeProducer:
    """Producteur Kafka qui garde les messages en mémoire."""

    def __init__(self) -> None:
        self.messages: list[tuple[str, str, bytes]] = []
        self.flushed = False

    def produce(self, topic: str, key: str, value: bytes) -> None:
        self.messages.append((topic, key, value))

    def flush(self, timeout: float) -> int:
        self.flushed = True
        return 0
