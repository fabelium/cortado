"""HTTP client adapter.

``HttpClient`` wraps a single reusable ``requests.Session`` and adds retries
with linear backoff, translating an exhausted retry budget into a domain
``NetworkError``. Keeping this behind one class means the rest of the code never
touches ``requests`` directly.
"""

from __future__ import annotations

import time

import requests

from coffee.config import Settings
from coffee.domain.errors import NetworkError


class HttpClient:
    """Adapter over ``requests.Session`` with retries and backoff."""

    def __init__(self, settings: Settings) -> None:
        self._settings = settings
        self._session = requests.Session()
        self._session.headers.update({"User-Agent": settings.user_agent})

    @property
    def session(self) -> requests.Session:
        """Expose the underlying session for adapters that need it directly."""
        return self._session

    def get(self, url: str, *, stream: bool = False) -> requests.Response:
        """GET with retries and linear backoff.

        Raises ``NetworkError`` if every attempt fails. With ``stream=True`` the
        body is not consumed, so large files can be downloaded in chunks.
        """
        last_error: Exception | None = None
        retries = self._settings.download_retries
        for attempt in range(1, retries + 1):
            try:
                response = self._session.get(
                    url, timeout=self._settings.http_timeout, stream=stream
                )
                response.raise_for_status()
                return response
            except requests.RequestException as error:
                last_error = error
                response = getattr(error, "response", None)
                if response is not None and 400 <= response.status_code < 500:
                    # Client errors are deterministic; retrying is pointless.
                    raise NetworkError(
                        f"{url} answered {response.status_code} (client error, "
                        "not retried)."
                    ) from error
                if attempt < retries:
                    time.sleep(self._settings.retry_backoff * attempt)
        raise NetworkError(
            f"Could not reach {url} after {retries} attempts: {last_error}"
        ) from last_error
