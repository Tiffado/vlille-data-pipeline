"""In-memory test doubles for GCS, BigQuery and Kafka."""


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
    """In-memory bucket, limited to what the project uses."""

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
    """Records load requests instead of running them."""

    def __init__(self) -> None:
        self.loads: list[tuple[str, list[dict], object]] = []

    def load_table_from_json(self, rows, table, job_config):
        self.loads.append((table, rows, job_config))
        return FakeLoadJob()


class FakeProducer:
    """Keeps produced messages in memory."""

    def __init__(self) -> None:
        self.messages: list[tuple[str, str, bytes]] = []
        self.flushed = False

    def produce(self, topic: str, key: str, value: bytes) -> None:
        self.messages.append((topic, key, value))

    def flush(self, timeout: float) -> int:
        self.flushed = True
        return 0


class FakeMessage:
    """Minimal Kafka message: partition, offset and value."""

    def __init__(self, partition: int, offset: int, value: bytes) -> None:
        self._partition = partition
        self._offset = offset
        self._value = value

    def partition(self) -> int:
        return self._partition

    def offset(self) -> int:
        return self._offset

    def value(self) -> bytes:
        return self._value


class FakeConsumer:
    """Records which files exist in the bucket when offsets are committed."""

    def __init__(self, bucket: FakeBucket) -> None:
        self._bucket = bucket
        self.objects_at_commit: list[str] | None = None

    def commit(self, asynchronous: bool) -> None:
        self.objects_at_commit = sorted(self._bucket.objects)
