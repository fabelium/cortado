"""Downloader chain: a connection drop mid-stream must surface as NetworkError
so FallbackDownloader hands over to yt-dlp; the yt-dlp adapter caps its
subprocess with a timeout and maps a hang to a domain AudioError.
Run: python3 tests/test_downloader.py
"""

import subprocess
import sys
from pathlib import Path
from types import SimpleNamespace

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import requests

from coffee.audio import downloader as downloader_module
from coffee.audio.downloader import (
    FallbackDownloader,
    HttpAudioDownloader,
    YtDlpAudioDownloader,
)
from coffee.domain.errors import AudioError, NetworkError


class _DroppingResponse:
    """Streams one chunk, then the connection drops mid-download."""

    headers = {"Content-Length": "131072"}

    def iter_content(self, chunk_size):
        yield b"x" * 100
        raise requests.ConnectionError("connection reset mid-stream")


class _DroppingHttp:
    """Stands in for HttpClient: the GET succeeds, the body stream fails."""

    def get(self, url, *, stream=False):
        return _DroppingResponse()


class _RecordingDownloader:
    def __init__(self):
        self.calls = []

    def download(self, url, dest, *, progress=None):
        self.calls.append(url)


def test_mid_download_failure_raises_network_error(tmp_path):
    dest = tmp_path / "audio.mp3"
    try:
        HttpAudioDownloader(_DroppingHttp()).download("http://x/a.mp3", dest)
    except NetworkError:
        pass  # expected: raw requests errors must become domain NetworkError
    else:
        raise AssertionError("a mid-download drop must raise NetworkError")
    assert not dest.exists()
    assert not dest.with_suffix(".part").exists()  # partial file cleaned up


def test_mid_download_failure_triggers_the_fallback(tmp_path):
    fallback = _RecordingDownloader()
    chain = FallbackDownloader(
        primary=HttpAudioDownloader(_DroppingHttp()), fallback=fallback
    )
    chain.download("http://x/a.mp3", tmp_path / "audio.mp3")
    assert fallback.calls == ["http://x/a.mp3"]


def _with_fakes(fn, *, run, which=lambda _name: "/usr/bin/yt-dlp"):
    """Call ``fn`` with subprocess.run and shutil.which patched in the module."""
    original_run = downloader_module.subprocess.run
    original_which = downloader_module.shutil.which
    downloader_module.subprocess.run = run
    downloader_module.shutil.which = which
    try:
        return fn()
    finally:
        downloader_module.subprocess.run = original_run
        downloader_module.shutil.which = original_which


def test_ytdlp_passes_its_timeout_to_subprocess(tmp_path):
    seen = {}
    dest = tmp_path / "audio.mp3"

    def fake_run(cmd, **kwargs):
        seen.update(kwargs)
        dest.write_bytes(b"mp3")
        return SimpleNamespace(returncode=0, stdout="", stderr="")

    downloader = YtDlpAudioDownloader(timeout=1234)
    _with_fakes(lambda: downloader.download("http://x/audio.mp3", dest), run=fake_run)
    assert seen["timeout"] == 1234


def test_ytdlp_separates_the_url_from_flags_with_a_terminator(tmp_path):
    seen = {}
    dest = tmp_path / "audio.mp3"

    def fake_run(cmd, **kwargs):
        seen["cmd"] = cmd
        dest.write_bytes(b"mp3")
        return SimpleNamespace(returncode=0, stdout="", stderr="")

    downloader = YtDlpAudioDownloader(timeout=60)
    _with_fakes(lambda: downloader.download("http://x/a.mp3", dest), run=fake_run)
    # a url can never be parsed as a yt-dlp flag
    assert seen["cmd"][-2:] == ["--", "http://x/a.mp3"]


def test_ytdlp_refuses_non_http_urls(tmp_path):
    calls = []

    def fake_run(cmd, **kwargs):
        calls.append(cmd)
        return SimpleNamespace(returncode=0, stdout="", stderr="")

    downloader = YtDlpAudioDownloader(timeout=60)
    try:
        _with_fakes(
            lambda: downloader.download("file:///etc/passwd", tmp_path / "a.mp3"),
            run=fake_run,
        )
    except AudioError:
        pass  # expected: only http(s) enclosure urls reach the subprocess
    else:
        raise AssertionError("a non-http url must raise AudioError")
    assert calls == []


def test_ytdlp_timeout_becomes_audio_error(tmp_path):
    def fake_run(cmd, **kwargs):
        raise subprocess.TimeoutExpired(cmd, kwargs.get("timeout", 1))

    downloader = YtDlpAudioDownloader(timeout=1)
    try:
        _with_fakes(
            lambda: downloader.download("http://x/audio.mp3", tmp_path / "a.mp3"),
            run=fake_run,
        )
    except AudioError as error:
        assert "timed out" in str(error)
    else:
        raise AssertionError("a hung yt-dlp must raise AudioError, not hang")


if __name__ == "__main__":
    import tempfile

    fns = [v for k, v in sorted(globals().items()) if k.startswith("test_")]
    for fn in fns:
        with tempfile.TemporaryDirectory() as tmp:
            fn(Path(tmp))
        print(f"  ok  {fn.__name__}")
    print(f"\n{len(fns)} tests OK")
