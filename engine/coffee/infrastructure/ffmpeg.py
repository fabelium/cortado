"""ffmpeg/ffprobe adapter.

``FFmpeg`` is the single seam between the application and the ffmpeg binaries.
It encapsulates every audio operation the tool needs (cut, re-encode to a
uniform format, generate silence, probe duration, concatenate) and turns any
failure into a domain ``AudioError``. Encoding parameters come from ``Settings``
so the rest of the code never hard-codes a bitrate or sample rate.
"""

from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

from coffee.config import Settings
from coffee.domain.errors import AudioError


class FFmpeg:
    """Adapter over the ffmpeg/ffprobe command-line tools."""

    def __init__(self, settings: Settings) -> None:
        self._settings = settings

    # --- internal helpers ---------------------------------------------------

    @staticmethod
    def _ensure_ffmpeg() -> None:
        if shutil.which("ffmpeg") is None:
            raise AudioError(
                "'ffmpeg' was not found on the PATH. Install it (e.g. "
                "'sudo apt install ffmpeg' or 'brew install ffmpeg')."
            )

    def _run(self, cmd: list[str]) -> None:
        """Run a command, turning a non-zero exit or a hang into ``AudioError``."""
        try:
            proc = subprocess.run(
                cmd, capture_output=True, text=True,
                timeout=self._settings.ffmpeg_timeout,
            )
        except subprocess.TimeoutExpired as error:
            raise AudioError(
                f"{cmd[0]} timed out after {self._settings.ffmpeg_timeout}s"
            ) from error
        if proc.returncode != 0:
            detail = (proc.stderr or proc.stdout).strip().splitlines()
            message = detail[-1] if detail else "no detail"
            raise AudioError(f"ffmpeg failed (code {proc.returncode}): {message}")

    def _encoding_args(self) -> list[str]:
        """Common args that force the uniform output format."""
        return [
            "-ar", self._settings.audio_sample_rate,
            "-ac", self._settings.audio_channels,
            "-b:a", self._settings.output_bitrate,
        ]

    # --- public operations --------------------------------------------------

    def cut_fragment(self, src: Path, start: int, end: int | None, dest: Path) -> None:
        """Extract ``[start, end)`` from ``src`` into ``dest``, re-encoding to MP3.

        Re-encoding guarantees second-accurate cuts and that every fragment
        shares the same format (key for a clean concatenation). When ``end`` is
        ``None`` the cut runs to the end of the file.
        """
        self._ensure_ffmpeg()
        cmd = [
            "ffmpeg", "-y", "-hide_banner", "-loglevel", "error",
            "-ss", str(start), "-i", str(src),
        ]
        if end is not None:
            cmd += ["-t", str(max(0, end - start))]
        cmd += ["-vn", *self._encoding_args(), str(dest)]
        self._run(cmd)

    def to_uniform_mp3(self, src: Path, dest: Path, tempo: float | None = None) -> None:
        """Re-encode ``src`` to the uniform format (44.1 kHz, stereo, 192 kbps).

        Used so TTS announcements share the fragments' format and concatenation
        can copy the stream without re-encoding. ``tempo`` speeds the audio up
        (ffmpeg ``atempo``: rate changes, pitch does not) — used to compensate
        gTTS's slow speech.
        """
        self._ensure_ffmpeg()
        cmd = ["ffmpeg", "-y", "-hide_banner", "-loglevel", "error", "-i", str(src), "-vn"]
        if tempo and tempo != 1.0:
            cmd += ["-filter:a", f"atempo={tempo}"]
        cmd += [*self._encoding_args(), str(dest)]
        self._run(cmd)

    def make_silence(self, seconds: float, dest: Path) -> None:
        """Generate a uniform-format MP3 of silence, used as a separator."""
        self._ensure_ffmpeg()
        self._run([
            "ffmpeg", "-y", "-hide_banner", "-loglevel", "error",
            "-f", "lavfi",
            "-i", f"anullsrc=r={self._settings.audio_sample_rate}:cl=stereo",
            "-t", f"{seconds}",
            "-b:a", self._settings.output_bitrate,
            str(dest),
        ])

    def probe_duration(self, path: Path) -> float:
        """Return the real duration of an audio file in seconds (via ffprobe)."""
        if shutil.which("ffprobe") is None:
            raise AudioError("'ffprobe' was not found (it ships with ffmpeg).")
        try:
            proc = subprocess.run(
                ["ffprobe", "-v", "error", "-show_entries", "format=duration",
                 "-of", "default=nokey=1:noprint_wrappers=1", str(path)],
                capture_output=True, text=True,
                timeout=self._settings.ffmpeg_timeout,
            )
        except subprocess.TimeoutExpired as error:
            raise AudioError(
                f"ffprobe timed out after {self._settings.ffmpeg_timeout}s"
            ) from error
        try:
            return float(proc.stdout.strip())
        except ValueError as error:
            raise AudioError(f"Could not measure the duration of {path}") from error

    def concat(self, parts: list[Path], dest: Path) -> None:
        """Join ``parts`` (in order) into a single MP3.

        Uses ffmpeg's 'concat demuxer'. Since the parts are already uniform, it
        first tries to copy the stream (``-c copy``, lossless and instant) and
        falls back to re-encoding if that fails.
        """
        self._ensure_ffmpeg()
        if not parts:
            raise AudioError("No fragments to concatenate.")

        list_file = dest.with_suffix(".concat.txt")
        # concat-demuxer quoting: a literal ' inside a quoted path becomes '\''
        quoted = ("'" + str(p.resolve()).replace("'", "'\\''") + "'" for p in parts)
        list_file.write_text(
            "".join(f"file {q}\n" for q in quoted), encoding="utf-8"
        )
        base = [
            "ffmpeg", "-y", "-hide_banner", "-loglevel", "error",
            "-f", "concat", "-safe", "0", "-i", str(list_file),
        ]
        try:
            try:
                self._run(base + ["-c", "copy", str(dest)])
            except AudioError:
                # Fallback: re-encode to the uniform format.
                self._run(base + [*self._encoding_args(), str(dest)])
        finally:
            list_file.unlink(missing_ok=True)
