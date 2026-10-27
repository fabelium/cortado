"""FFmpeg adapter: every subprocess call carries the Settings timeout so a hung
ffmpeg/ffprobe cannot block the engine, and a timeout surfaces as a domain
AudioError. Run: python3 tests/test_ffmpeg.py
"""

import subprocess
import sys
from pathlib import Path
from types import SimpleNamespace

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from coffee.config import Settings
from coffee.domain.errors import AudioError
from coffee.infrastructure import ffmpeg as ffmpeg_module
from coffee.infrastructure.ffmpeg import FFmpeg


def _with_fakes(fn, *, run, which=lambda _name: "/usr/bin/ffmpeg"):
    """Call ``fn`` with subprocess.run and shutil.which patched in the module."""
    original_run = ffmpeg_module.subprocess.run
    original_which = ffmpeg_module.shutil.which
    ffmpeg_module.subprocess.run = run
    ffmpeg_module.shutil.which = which
    try:
        return fn()
    finally:
        ffmpeg_module.subprocess.run = original_run
        ffmpeg_module.shutil.which = original_which


def test_run_passes_the_settings_timeout():
    seen = {}

    def fake_run(cmd, **kwargs):
        seen.update(kwargs)
        return SimpleNamespace(returncode=0, stdout="", stderr="")

    settings = Settings()
    _with_fakes(lambda: FFmpeg(settings)._run(["ffmpeg", "-version"]), run=fake_run)
    assert seen["timeout"] == settings.ffmpeg_timeout
    assert settings.ffmpeg_timeout > 0


def test_run_timeout_becomes_audio_error():
    def fake_run(cmd, **kwargs):
        raise subprocess.TimeoutExpired(cmd, kwargs.get("timeout", 1))

    try:
        _with_fakes(lambda: FFmpeg(Settings())._run(["ffmpeg"]), run=fake_run)
    except AudioError as error:
        assert "timed out" in str(error)
    else:
        raise AssertionError("a hung ffmpeg must raise AudioError, not hang")


def test_probe_duration_passes_the_settings_timeout():
    seen = {}

    def fake_run(cmd, **kwargs):
        seen.update(kwargs)
        return SimpleNamespace(returncode=0, stdout="12.5\n", stderr="")

    settings = Settings()
    duration = _with_fakes(
        lambda: FFmpeg(settings).probe_duration(Path("/audio.mp3")), run=fake_run
    )
    assert duration == 12.5
    assert seen["timeout"] == settings.ffmpeg_timeout


def test_probe_duration_timeout_becomes_audio_error():
    def fake_run(cmd, **kwargs):
        raise subprocess.TimeoutExpired(cmd, kwargs.get("timeout", 1))

    try:
        _with_fakes(
            lambda: FFmpeg(Settings()).probe_duration(Path("/audio.mp3")),
            run=fake_run,
        )
    except AudioError as error:
        assert "timed out" in str(error)
    else:
        raise AssertionError("a hung ffprobe must raise AudioError, not hang")


def test_to_uniform_mp3_applies_the_requested_tempo():
    seen = {}

    def fake_run(cmd, **kwargs):
        seen["cmd"] = cmd
        return SimpleNamespace(returncode=0, stdout="", stderr="")

    _with_fakes(
        lambda: FFmpeg(Settings()).to_uniform_mp3(
            Path("/raw.mp3"), Path("/norm.mp3"), tempo=1.25
        ),
        run=fake_run,
    )
    assert "atempo=1.25" in " ".join(seen["cmd"])  # faster speech, same pitch


def test_to_uniform_mp3_without_tempo_does_not_filter():
    seen = {}

    def fake_run(cmd, **kwargs):
        seen["cmd"] = cmd
        return SimpleNamespace(returncode=0, stdout="", stderr="")

    _with_fakes(
        lambda: FFmpeg(Settings()).to_uniform_mp3(Path("/raw.mp3"), Path("/norm.mp3")),
        run=fake_run,
    )
    assert "atempo" not in " ".join(seen["cmd"])


def test_concat_manifest_escapes_single_quotes(tmp_path):
    captured = {}

    def fake_run(cmd, **kwargs):
        manifest = Path(cmd[cmd.index("-i") + 1])
        captured["manifest"] = manifest.read_text(encoding="utf-8")
        return SimpleNamespace(returncode=0, stdout="", stderr="")

    part = tmp_path / "l'episodio.mp3"
    part.write_bytes(b"mp3")
    _with_fakes(
        lambda: FFmpeg(Settings()).concat([part], tmp_path / "out.mp3"),
        run=fake_run,
    )
    line = captured["manifest"].strip()
    # concat-demuxer escaping: a ' inside a quoted path is written as '\''
    assert "l'\\''episodio.mp3" in line
    assert line.startswith("file '") and line.endswith("'")


if __name__ == "__main__":
    import tempfile

    fns = [v for k, v in sorted(globals().items()) if k.startswith("test_")]
    for fn in fns:
        if "tmp_path" in fn.__code__.co_varnames[: fn.__code__.co_argcount]:
            with tempfile.TemporaryDirectory() as tmp:
                fn(Path(tmp))
        else:
            fn()
        print(f"  ok  {fn.__name__}")
    print(f"\n{len(fns)} tests OK")
