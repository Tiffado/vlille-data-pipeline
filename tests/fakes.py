"""Doublures de test partagées."""

from google.api_core.exceptions import PreconditionFailed


class FakeBlob:
    def __init__(self, bucket: "FakeBucket", name: str) -> None:
        self._bucket = bucket
        self._name = name

    def upload_from_string(self, data, content_type, if_generation_match=None):
        if if_generation_match == 0 and self._name in self._bucket.objects:
            raise PreconditionFailed("objet déjà présent")
        self._bucket.objects[self._name] = data
        self._bucket.content_types[self._name] = content_type


class FakeBucket:
    """Bucket en mémoire : reproduit seulement ce que RawStore utilise."""

    def __init__(self) -> None:
        self.objects: dict[str, bytes] = {}
        self.content_types: dict[str, str] = {}

    def blob(self, name: str) -> FakeBlob:
        return FakeBlob(self, name)
