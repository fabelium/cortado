"""Application settings.

A single immutable ``Settings`` dataclass groups every tunable value: feed URL,
filesystem paths, audio encoding, network timeouts/retries, pause length and the
Spanish-language copy that is spoken to listeners. ``Settings.from_env`` allows
environment overrides where it is natural, while keeping sensible defaults so
the tool works out of the box.

The Spanish strings (podcast name, disclaimer) are intentionally NOT translated:
they are spoken/shown to a Spanish-speaking audience and must stay in Spanish.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path

# Engine root: .../cortado/engine/ (this file lives in engine/coffee/config.py).
_BASE_DIR = Path(__file__).resolve().parent.parent

# Disclaimer spoken at the start of every generated file. Kept in Spanish on
# purpose: it is read aloud to Spanish listeners. The comma keeps every
# punctuation-delimited segment under gTTS's ~100-char request limit —
# without it the first sentence is force-split between "inteligencia" and
# "artificial", which is heard as a broken pause (see tests/test_config.py).
_DEFAULT_DISCLAIMER = (
    "Este audio ha sido generado con fines educativos, dentro del máster de "
    "desarrollo con inteligencia artificial. Recomendamos escuchar los "
    "episodios completos en su fuente original."
)


@dataclass(frozen=True)
class Settings:
    """Immutable configuration shared across the application."""

    # --- Data source ---
    feed_url: str = "https://feeds.acast.com/public/shows/coffee-break-senal-y-ruido"
    user_agent: str = "Mozilla/5.0 (CoffeeClips; private local tool)"

    # --- Filesystem paths (relative to the project root: cortado/) ---
    base_dir: Path = _BASE_DIR
    cache_dir: Path = field(default=_BASE_DIR / "cache")
    episodes_dir: Path = field(default=_BASE_DIR / "cache" / "episodes")
    feed_cache_file: Path = field(default=_BASE_DIR / "cache" / "feed_cache.json")
    output_dir: Path = field(default=_BASE_DIR / "output")

    # --- Cache ---
    feed_max_age_hours: float = 24.0   # re-download the RSS when the cache is older

    # --- Output audio ---
    output_bitrate: str = "192k"
    audio_sample_rate: str = "44100"
    audio_channels: str = "2"

    # --- Announcements (spoken, Spanish) ---
    podcast_name: str = "Coffee Break, Señal y Ruido"
    intro_pause_seconds: float = 0.8   # separating silence right before each announcement
    disclaimer_text: str = _DEFAULT_DISCLAIMER
    tts_tempo: float = 1.25            # gTTS speaks slowly; speed announcements up (same pitch)

    # --- Network ---
    http_timeout: int = 30        # seconds per attempt
    download_retries: int = 3     # total attempts for the feed and downloads
    retry_backoff: float = 2.0    # base seconds; multiplied by the attempt number

    # --- Subprocess timeouts (a hung child must not hang the whole engine) ---
    ffmpeg_timeout: int = 600     # seconds per ffmpeg/ffprobe invocation
    ytdlp_timeout: int = 1800     # seconds for a full-episode yt-dlp download

    # --- Search ---
    many_results_warning: int = 25  # warn before downloading above this many fragments

    # --- Limits (defensive caps for the JSON engine entry point) ---
    max_selection: int = 50  # max fragments/sources per generate/transcribe request

    # --- AI (semantic search & relevance classification) ---
    embedding_model_local: str = (
        "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
    )
    embedding_model_gemini: str = "models/text-embedding-004"
    chat_model_gemini: str = "models/gemini-2.0-flash"
    semantic_top_k: int = 30          # max candidates kept from a semantic search
    semantic_threshold: float = 0.30  # min cosine similarity to keep a candidate

    def __post_init__(self) -> None:
        # ffmpeg's atempo filter only accepts 0.5-2.0; outside it the TTS
        # announcements would fail to encode and silently drop out of the clip.
        if not 0.5 <= self.tts_tempo <= 2.0:
            raise ValueError(f"tts_tempo must be within 0.5-2.0, got {self.tts_tempo}")

    @classmethod
    def from_env(cls) -> Settings:
        """Build settings, allowing a few natural environment overrides.

        Only values that a user might reasonably want to change per-run are
        exposed; everything else keeps its default.
        """
        overrides: dict[str, object] = {}
        if feed_url := os.environ.get("COFFEE_FEED_URL"):
            overrides["feed_url"] = feed_url
        if cache_dir := os.environ.get("COFFEE_CACHE_DIR"):
            cache_path = Path(cache_dir)
            overrides["cache_dir"] = cache_path
            overrides["episodes_dir"] = cache_path / "episodes"
            overrides["feed_cache_file"] = cache_path / "feed_cache.json"
        if output_dir := os.environ.get("COFFEE_OUTPUT_DIR"):
            overrides["output_dir"] = Path(output_dir)
        return cls(**overrides)
