"""Clip assembly service.

Given the fragments to include, ``ClipAssembler`` downloads the needed episodes,
builds per-fragment units (optional separating silence + spoken intro + the cut
fragment), packs whole units into duration blocks, prepends the disclaimer to
each block and concatenates everything into one or more MP3s.

Every collaborator (ffmpeg, downloader, TTS, announcements, cache) is injected
through the constructor: Dependency Injection keeps the assembler testable and
free of hidden globals. Graceful degradation is built in: a failed TTS or
disclaimer is reported but never aborts an otherwise valid MP3.
"""

from __future__ import annotations

import tempfile
from pathlib import Path
from typing import Callable

from coffee.audio.downloader import AudioDownloader, ProgressFn
from coffee.config import Settings
from coffee.domain.errors import TtsError
from coffee.domain.models import Episode, Fragment
from coffee.infrastructure.ffmpeg import FFmpeg
from coffee.infrastructure.json_cache import JsonCache
from coffee.speech.announcements import AnnouncementBuilder
from coffee.speech.text_to_speech import TextToSpeech

# A unit is (audio parts in order, total real duration in seconds).
Unit = tuple[list[Path], float]
# Status messages bubble up to the CLI without coupling the assembler to stdout.
Reporter = Callable[[str], None]


class ClipAssembler:
    """Builds the concatenated MP3(s) from a list of fragments (DI throughout)."""

    def __init__(
        self,
        settings: Settings,
        ffmpeg: FFmpeg,
        downloader: AudioDownloader,
        text_to_speech: TextToSpeech,
        announcements: AnnouncementBuilder,
        cache: JsonCache,
    ) -> None:
        self._settings = settings
        self._ffmpeg = ffmpeg
        self._downloader = downloader
        self._tts = text_to_speech
        self._announcements = announcements
        self._cache = cache

    # --- episode download ---------------------------------------------------

    def _episode_path(self, episode: Episode, progress: ProgressFn | None = None) -> Path:
        """Ensure the full episode MP3 is cached and return its path."""
        dest = self._cache.episode_audio_path(episode.guid)
        if self._cache.is_episode_downloaded(episode.guid):
            return dest
        self._settings.episodes_dir.mkdir(parents=True, exist_ok=True)
        self._downloader.download(episode.audio_url, dest, progress=progress)
        return dest

    def _download_episodes(
        self, fragments: list[Fragment], report: Reporter
    ) -> None:
        """Download only the distinct episodes involved (no duplicates)."""
        unique = {f.episode.guid: f.episode for f in fragments}
        report(f"\nDownloading {len(unique)} required episode(s)...")
        for index, episode in enumerate(unique.values(), 1):
            last_pct = -1

            def progress(done: int, total: int, _i=index, _ep=episode) -> None:
                nonlocal last_pct
                pct = done * 100 // total if total else 0
                if pct == last_pct:  # only refresh when the integer percent changes
                    return
                last_pct = pct
                report(
                    f"\r  [{_i}/{len(unique)}] {_ep.title[:45]:45} {pct:3d}%"
                )

            self._episode_path(episode, progress)
            report(f"\r  [{index}/{len(unique)}] {episode.title[:45]:45} done ")

    # --- announcements ------------------------------------------------------

    def _synthesize_uniform(self, text: str, raw: Path, norm: Path) -> Path:
        """Synthesize ``text`` to ``raw`` and re-encode it to the uniform format."""
        self._tts.synthesize(text, raw)
        self._ffmpeg.to_uniform_mp3(raw, norm, tempo=self._settings.tts_tempo)
        return norm

    # --- assembly -----------------------------------------------------------

    def assemble(
        self,
        fragments: list[Fragment],
        out_path: Path,
        *,
        keep_temp: bool,
        intro: bool,
        disclaimer: bool,
        split_seconds: int | None,
        report: Reporter = lambda _msg: None,
    ) -> list[Path]:
        """Download, cut, add announcements and concatenate. Returns the MP3s.

        - ``intro=True`` prepends a spoken announcement (episode + date) to each
          fragment.
        - ``disclaimer=True`` prepends the educational disclaimer to each file.
        - ``split_seconds=None`` produces a single file; otherwise whole
          fragments are grouped into blocks not exceeding that duration,
          producing several files suffixed ``_parteN``.

        The assembler is the single owner of the "chronological output" promise:
        whatever order the search returned (relevance for semantic search), the
        audio is always built oldest-first.
        """
        fragments = sorted(fragments, key=lambda fragment: fragment.date)
        self._download_episodes(fragments, report)

        tmp_dir = Path(tempfile.mkdtemp(prefix="coffeeclips_"))
        try:
            # Reusable separating silence (only when there is an intro).
            silence_path: Path | None = None
            if intro:
                silence_path = tmp_dir / "silence.mp3"
                self._ffmpeg.make_silence(
                    self._settings.intro_pause_seconds, silence_path
                )

            units = self._build_units(fragments, tmp_dir, intro, silence_path, report)
            disclaimer_parts = self._build_disclaimer(
                tmp_dir, disclaimer, silence_path, report
            )

            # Group into blocks (a single one without --split) and concatenate.
            out_path.parent.mkdir(parents=True, exist_ok=True)
            blocks = self._pack_blocks(units, split_seconds)
            multiple = len(blocks) > 1
            outputs: list[Path] = []
            report(f"\nConcatenating {len(blocks)} file(s)...")
            for number, block in enumerate(blocks, 1):
                parts = list(disclaimer_parts)
                parts += [part for unit_parts, _ in block for part in unit_parts]
                dest = self._block_path(out_path, number) if multiple else out_path
                self._ffmpeg.concat(parts, dest)
                outputs.append(dest)
            return outputs
        finally:
            if keep_temp:
                report(f"(temporary fragments kept in {tmp_dir})")
            else:
                for part in tmp_dir.glob("*"):
                    part.unlink(missing_ok=True)
                tmp_dir.rmdir()

    def _build_units(
        self,
        fragments: list[Fragment],
        tmp_dir: Path,
        intro: bool,
        silence_path: Path | None,
        report: Reporter,
    ) -> list[Unit]:
        """Build a unit (optional silence + intro + cut fragment) per fragment."""
        units: list[Unit] = []
        report(
            f"\nPreparing {len(fragments)} fragment(s)"
            f"{' with announcement' if intro else ''}..."
        )
        for index, fragment in enumerate(fragments, 1):
            src = self._episode_path(fragment.episode)  # already cached
            unit_parts: list[Path] = []
            if intro:
                try:
                    raw = tmp_dir / f"intro_{index:03d}_raw.mp3"
                    norm = tmp_dir / f"intro_{index:03d}.mp3"
                    self._synthesize_uniform(
                        self._announcements.for_episode(fragment.episode), raw, norm
                    )
                    if silence_path is not None:
                        unit_parts.append(silence_path)  # separating pause
                    unit_parts.append(norm)              # announcement
                except TtsError as error:
                    report(f"  ! no announcement for #{index}: {error}")
            frag_part = tmp_dir / f"frag_{index:03d}.mp3"
            self._ffmpeg.cut_fragment(
                src, fragment.topic.start, fragment.topic.end, frag_part
            )
            unit_parts.append(frag_part)
            duration = sum(self._ffmpeg.probe_duration(p) for p in unit_parts)
            units.append((unit_parts, duration))
            report(f"  [{index}/{len(fragments)}] {fragment.topic.name[:55]}")
        return units

    def _build_disclaimer(
        self,
        tmp_dir: Path,
        disclaimer: bool,
        silence_path: Path | None,
        report: Reporter,
    ) -> list[Path]:
        """Synthesize the educational disclaimer placed at the start of each file."""
        if not disclaimer:
            return []
        try:
            raw = tmp_dir / "disclaimer_raw.mp3"
            norm = tmp_dir / "disclaimer.mp3"
            self._synthesize_uniform(self._announcements.disclaimer, raw, norm)
            parts = [norm]
            if silence_path is not None:
                parts.append(silence_path)
            return parts
        except TtsError as error:
            report(f"  ! no disclaimer: {error}")
            return []

    @staticmethod
    def _pack_blocks(units: list[Unit], split_seconds: int | None) -> list[list[Unit]]:
        """Distribute whole units into blocks not exceeding ``split_seconds``.

        Without split -> a single block with everything. A unit longer than the
        limit forms its own block (a fragment is never cut in half).
        """
        if not split_seconds:
            return [units]
        blocks: list[list[Unit]] = []
        current: list[Unit] = []
        acc = 0.0
        for unit in units:
            duration = unit[1]
            if current and acc + duration > split_seconds:
                blocks.append(current)
                current, acc = [], 0.0
            current.append(unit)
            acc += duration
        if current:
            blocks.append(current)
        return blocks

    @staticmethod
    def _block_path(out_path: Path, number: int) -> Path:
        """output/topic_date.mp3 -> output/topic_date_parteN.mp3."""
        return out_path.with_name(f"{out_path.stem}_parte{number}{out_path.suffix}")
