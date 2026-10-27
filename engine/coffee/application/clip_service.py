"""End-to-end use-case orchestrator (Facade pattern).

``ClipService`` ties together the repository, the search service, the clip
assembler, the transcriber and the e-mail sender into a single, stateless
use case. It exposes small, intention-revealing methods that the CLI (or a
future worker) can call without knowing about the underlying collaborators.

It is deliberately stateless and queue-friendly: it holds no per-request state,
so it can be driven later by an asynchronous worker (e.g. a Laravel queue/job
layer). The queue/Redis machinery lives in that future layer, NOT here.
"""

from __future__ import annotations

from pathlib import Path
from typing import Callable

from coffee.application.clip_assembler import ClipAssembler, Reporter
from coffee.delivery.email_sender import EmailSender
from coffee.domain.models import Episode, Fragment, SearchHit
from coffee.feed.episode_repository import EpisodeRepository
from coffee.search.search_service import SearchService
from coffee.speech.transcriber import Transcriber


class ClipService:
    """Facade over repository + search + assembler + transcriber + e-mail."""

    def __init__(
        self,
        repository: EpisodeRepository,
        search_service: SearchService,
        assembler: ClipAssembler,
        transcriber: Transcriber,
        email_sender: EmailSender,
    ) -> None:
        self._repository = repository
        self._search = search_service
        self._assembler = assembler
        self._transcriber = transcriber
        self._email = email_sender

    def load_episodes(self, *, force_refresh: bool = False) -> list[Episode]:
        return self._repository.get_episodes(force_refresh=force_refresh)

    def search(self, episodes: list[Episode], query: str) -> list[SearchHit]:
        return self._search.search(episodes, query)

    def build_clips(
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
        return self._assembler.assemble(
            fragments,
            out_path,
            keep_temp=keep_temp,
            intro=intro,
            disclaimer=disclaimer,
            split_seconds=split_seconds,
            report=report,
        )

    def transcribe(self, audio_path: Path) -> dict[str, Path]:
        return self._transcriber.transcribe(audio_path)

    def send_email(
        self, path: Path, subject: str, body: str, recipient: str | None = None
    ) -> str:
        return self._email.send_file(path, subject, body, to_addr=recipient)
