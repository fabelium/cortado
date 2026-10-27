"""HttpClient retries: transient failures (5xx, connection errors) are retried
with backoff, but 4xx client errors fail fast — retrying a 404 is pointless.
Run: python3 tests/test_http_client.py
"""

import sys
from pathlib import Path
from types import SimpleNamespace

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import requests

from coffee.config import Settings
from coffee.domain.errors import NetworkError
from coffee.infrastructure.http_client import HttpClient


class _FailingSession:
    """Fake requests.Session whose every GET fails with the given status."""

    def __init__(self, status):
        self._status = status
        self.calls = 0

    def get(self, url, *, timeout=None, stream=False):
        self.calls += 1
        error = requests.HTTPError(
            f"{self._status} error", response=SimpleNamespace(status_code=self._status)
        )
        return SimpleNamespace(raise_for_status=_raiser(error))


def _raiser(error):
    def raise_for_status():
        raise error

    return raise_for_status


def _client(status):
    client = HttpClient(Settings(retry_backoff=0.0))
    session = _FailingSession(status)
    client._session = session
    return client, session


def test_4xx_fails_fast_without_retries():
    client, session = _client(404)
    try:
        client.get("http://x/missing.mp3")
    except NetworkError as error:
        assert "404" in str(error)
    else:
        raise AssertionError("a 404 must raise NetworkError")
    assert session.calls == 1  # was: retried 3 times with backoff


def test_5xx_is_still_retried():
    client, session = _client(503)
    try:
        client.get("http://x/flaky.mp3")
    except NetworkError:
        pass  # expected after the retry budget is exhausted
    else:
        raise AssertionError("an exhausted retry budget must raise NetworkError")
    assert session.calls == Settings().download_retries


if __name__ == "__main__":
    fns = [v for k, v in sorted(globals().items()) if k.startswith("test_")]
    for fn in fns:
        fn()
        print(f"  ok  {fn.__name__}")
    print(f"\n{len(fns)} tests OK")
