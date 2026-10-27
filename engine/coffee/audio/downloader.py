"""Episode downloaders (Strategy + Chain-of-responsibility).

``AudioDownloader`` is the port. Two adapters implement it:

- ``HttpAudioDownloader`` streams the MP3 with the shared ``HttpClient``,
  writing to a ``.part`` file and renaming on success (atomic), reporting
  progress through a callback.
- ``YtDlpAudioDownloader`` shells out to ``yt-dlp`` as a fallback for
  CDN-hostile URLs.

``FallbackDownloader`` composes them as a small chain of responsibility: HTTP
first, yt-dlp only when the HTTP attempt raises ``NetworkError``.
"""

from __future__ import annotations

import shutil
import subprocess
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Callable
from urllib.parse import urlparse

import requests

from coffee.config import Settings
from coffee.domain.errors import AudioError, NetworkError
from coffee.infrastructure.http_client import HttpClient

# done_bytes, total_bytes -> None
ProgressFn = Callable[[int, int], None]


class AudioDownloader(ABC):
    """Port: download the audio at ``url`` to ``dest``."""

    @abstractmethod
    def download(
        self, url: str, dest: Path, *, progress: ProgressFn | None = None
    ) -> None:
        raise NotImplementedError


class HttpAudioDownloader(AudioDownloader):
    """Adapter: stream the MP3 over HTTP to an atomic ``.part`` file."""

    def __init__(self, http_client: HttpClient) -> None:
        self._http = http_client

    def download(
        self, url: str, dest: Path, *, progress: ProgressFn | None = None
    ) -> None:
        response = self._http.get(url, stream=True)
        total = int(response.headers.get("Content-Length", 0))
        downloaded = 0
        tmp = dest.with_suffix(".part")
        try:
            with open(tmp, "wb") as handle:
                for chunk in response.iter_content(chunk_size=65536):
                    if not chunk:
                        continue
                    handle.write(chunk)
                    downloaded += len(chunk)
                    if progress:
                        progress(downloaded, total)
            tmp.replace(dest)
        except requests.RequestException as error:
            # A drop mid-stream must look like any other network failure so
            # FallbackDownloader can hand over to yt-dlp.
            raise NetworkError(f"Download of {url} was interrupted: {error}") from error
        finally:
            tmp.unlink(missing_ok=True)


class YtDlpAudioDownloader(AudioDownloader):
    """Adapter: download with ``yt-dlp`` (fallback for problematic CDNs)."""

    def __init__(self, timeout: int) -> None:
        self._timeout = timeout

    def download(
        self, url: str, dest: Path, *, progress: ProgressFn | None = None
    ) -> None:
        if urlparse(url).scheme.lower() not in ("http", "https"):
            raise AudioError(f"yt-dlp fallback only accepts http(s) urls, got: {url}")
        if shutil.which("yt-dlp") is None:
            raise AudioError("Direct download failed and yt-dlp is unavailable.")
        try:
            proc = subprocess.run(
                ["yt-dlp", "--quiet", "--no-warnings", "--no-playlist", "--no-part",
                 "-o", str(dest), "--", url],
                capture_output=True, text=True, timeout=self._timeout,
            )
        except subprocess.TimeoutExpired as error:
            raise AudioError(
                f"yt-dlp timed out after {self._timeout}s for {url}"
            ) from error
        if proc.returncode != 0:
            detail = (proc.stderr or proc.stdout).strip().splitlines()
            message = detail[-1] if detail else "no detail"
            raise AudioError(f"yt-dlp failed (code {proc.returncode}): {message}")
        if not (dest.exists() and dest.stat().st_size > 0):
            raise AudioError(f"yt-dlp produced no audio for {url}")


class FallbackDownloader(AudioDownloader):
    """Chain of responsibility: try the primary, fall back on ``NetworkError``.

    The primary (HTTP) handles the request; only when it gives up with a
    ``NetworkError`` does the next downloader (yt-dlp) take over.
    """

    def __init__(self, primary: AudioDownloader, fallback: AudioDownloader) -> None:
        self._primary = primary
        self._fallback = fallback

    def download(
        self, url: str, dest: Path, *, progress: ProgressFn | None = None
    ) -> None:
        try:
            self._primary.download(url, dest, progress=progress)
        except NetworkError:
            self._fallback.download(url, dest, progress=progress)


def build_default_downloader(
    settings: Settings, http_client: HttpClient
) -> AudioDownloader:
    """Wire the default HTTP -> yt-dlp fallback chain."""
    return FallbackDownloader(
        primary=HttpAudioDownloader(http_client),
        fallback=YtDlpAudioDownloader(timeout=settings.ytdlp_timeout),
    )
