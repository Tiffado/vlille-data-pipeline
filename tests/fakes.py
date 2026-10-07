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


class FakeMessage:
    """Message Kafka minimal : partition, offset, horodatage (ms) et valeur."""

    def __init__(self, partition: int, offset: int, value: bytes, timestamp_ms: int) -> None:
        self._partition = partition
        self._offset = offset
        self._value = value
        self._timestamp_ms = timestamp_ms

    def partition(self) -> int:
        return self._partition

    def offset(self) -> int:
        return self._offset

    def value(self) -> bytes:
        return self._value

    def timestamp(self) -> tuple[int, int]:
        return 1, self._timestamp_ms


class FakeConsumer:
    """Consommateur Kafka qui note l'état du bucket au moment du commit."""

    def __init__(self, bucket: FakeBucket) -> None:
        self._bucket = bucket
        self.objects_at_commit: list[str] | None = None

    def commit(self, asynchronous: bool) -> None:
        self.objects_at_commit = sorted(self._bucket.objects)
