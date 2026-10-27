"""Command-line interface and composition root.

This module is the single place where concrete adapters are instantiated and
wired together (Dependency Injection) into a ``ClipService``. It parses the CLI
arguments, drives the use case, prints progress and maps results to exit codes.
Keeping all the wiring here means the rest of the package stays free of
construction concerns and is straightforward to test or to reuse from another
front end (e.g. a future web worker).
"""

from __future__ import annotations

import argparse
import re
import sys
from datetime import datetime
from pathlib import Path

from coffee.ai.provider_factory import ProviderFactory
from coffee.ai.relevance_classifier import RelevanceClassifier
from coffee.application.clip_assembler import ClipAssembler
from coffee.application.clip_service import ClipService
from coffee.audio.downloader import build_default_downloader
from coffee.audio.episode_audio import EpisodeAudioProvider
from coffee.config import Settings
from coffee.delivery.email_sender import EmailSender
from coffee.domain.errors import CoffeeError, MailError
from coffee.domain.models import SearchHit
from coffee.feed.episode_repository import EpisodeRepository
from coffee.feed.feed_source import FeedSource
from coffee.infrastructure.embedding_cache import EmbeddingCache
from coffee.infrastructure.ffmpeg import FFmpeg
from coffee.infrastructure.http_client import HttpClient
from coffee.infrastructure.json_cache import JsonCache
from coffee.infrastructure.pandoc import PandocExporter
from coffee.knowledge.book_composer import BookComposer
from coffee.knowledge.chunker import PassageChunker
from coffee.knowledge.fragment_transcriber import FragmentTranscriber
from coffee.knowledge.indexing import build_passage_index
from coffee.knowledge.markdown_renderer import MarkdownRenderer
from coffee.knowledge.outline_generator import OutlineGenerator
from coffee.knowledge.rag_answerer import RagAnswer
from coffee.knowledge.rag_service import RagService
from coffee.knowledge.section_writer import SectionWriter
from coffee.knowledge.transcript_store import TranscriptStore
from coffee.parsing.description_parser import DescriptionParser
from coffee.search.search_service import SearchService
from coffee.search.search_strategy import KeywordSearchStrategy
from coffee.search.semantic_search_strategy import SemanticSearchStrategy
from coffee.search.text import normalize
from coffee.speech.announcements import AnnouncementBuilder
from coffee.speech.text_to_speech import GttsTextToSpeech
from coffee.speech.transcriber import FasterWhisperTranscriber


# --- composition root -----------------------------------------------------

def build_search_service(
    settings: Settings, args: argparse.Namespace
) -> SearchService:
    """Choose and wire the search strategy from the CLI arguments (Factory).

    Default is the keyword strategy. ``--semantic`` swaps in embedding-based
    search (provider chosen by ``--model``), and ``--classify`` adds an LLM
    relevance filter on top. Building the providers is cheap: the local model is
    loaded lazily, only when a search actually runs.
    """
    if not args.semantic:
        return SearchService(KeywordSearchStrategy())

    factory = ProviderFactory(settings)
    embeddings = factory.embedding_provider(args.model)
    classifier = None
    if args.classify:
        classifier = RelevanceClassifier(factory.chat_model("gemini"))

    # Tuning comes from the request/CLI when given, else the settings defaults.
    # Note the explicit None checks: a threshold of 0.0 is a valid value.
    top_k = getattr(args, "top_k", None)
    threshold = getattr(args, "threshold", None)
    strategy = SemanticSearchStrategy(
        embeddings,
        EmbeddingCache(settings, embeddings.model_id),
        top_k=settings.semantic_top_k if top_k is None else top_k,
        threshold=settings.semantic_threshold if threshold is None else threshold,
        classifier=classifier,
        report=_report,
    )
    return SearchService(strategy)


def build_service(
    settings: Settings, search_service: SearchService
) -> tuple[ClipService, JsonCache]:
    """Instantiate and wire every concrete adapter into a ``ClipService``.

    Returns the service plus the cache (the CLI needs the cache directly for
    ``--clean-cache``).
    """
    http_client = HttpClient(settings)
    cache = JsonCache(settings)
    ffmpeg = FFmpeg(settings)

    feed_source = FeedSource(settings, http_client, DescriptionParser())
    repository = EpisodeRepository(feed_source, cache)

    assembler = ClipAssembler(
        settings=settings,
        ffmpeg=ffmpeg,
        downloader=build_default_downloader(settings, http_client),
        text_to_speech=GttsTextToSpeech(language="es"),
        announcements=AnnouncementBuilder(settings),
        cache=cache,
    )

    service = ClipService(
        repository=repository,
        search_service=search_service,
        assembler=assembler,
        transcriber=FasterWhisperTranscriber(),
        email_sender=EmailSender(),
    )
    return service, cache


def build_rag_service(settings: Settings, *, model: str = "local") -> RagService:
    """Wire the RAG read side: fragment audio -> transcript -> chunks -> answerer.

    The transcript producer (``FragmentTranscriber``) cuts each selected fragment
    and transcribes it; results are cached forever by ``TranscriptStore`` keyed by
    fragment id. Embeddings index the passages (``model``: 'local' free/offline or
    'gemini'); the chat model that grounds answers is Gemini (needs GEMINI_API_KEY,
    loaded lazily on first use).
    """
    http_client = HttpClient(settings)
    cache = JsonCache(settings)
    ffmpeg = FFmpeg(settings)
    downloader = build_default_downloader(settings, http_client)

    episode_audio = EpisodeAudioProvider(settings, cache, downloader)
    producer = FragmentTranscriber(ffmpeg, FasterWhisperTranscriber(), episode_audio)
    store = TranscriptStore(settings.cache_dir / "transcripts.json", producer)

    factory = ProviderFactory(settings)
    return RagService(
        transcript_store=store,
        chunker=PassageChunker(),
        embeddings=factory.embedding_provider(model),
        chat=factory.chat_model("gemini"),
    )


def build_book_composer(settings: Settings, *, model: str = "local") -> BookComposer:
    """Wire the book read side: transcripts -> outline + retrieval-written sections.

    Reuses the same transcript producer and passage index as the RAG chat; the
    outline and sections are produced by the Gemini chat model (needs
    GEMINI_API_KEY, loaded lazily). ``model`` selects the embedding provider.
    """
    http_client = HttpClient(settings)
    cache = JsonCache(settings)
    ffmpeg = FFmpeg(settings)
    downloader = build_default_downloader(settings, http_client)

    episode_audio = EpisodeAudioProvider(settings, cache, downloader)
    producer = FragmentTranscriber(ffmpeg, FasterWhisperTranscriber(), episode_audio)
    store = TranscriptStore(settings.cache_dir / "transcripts.json", producer)
    chunker = PassageChunker()

    factory = ProviderFactory(settings)
    embeddings = factory.embedding_provider(model)
    chat = factory.chat_model("gemini")

    return BookComposer(
        store,
        OutlineGenerator(chat),
        SectionWriter(chat),
        index_builder=lambda fragments: build_passage_index(
            fragments, store, chunker, embeddings
        ),
    )


# --- presentation helpers -------------------------------------------------

def format_hms(seconds: int | None) -> str:
    """360 -> '6:00' ; 4140 -> '1:09:00' ; None -> 'end'."""
    if seconds is None:
        return "end"
    hours, rem = divmod(seconds, 3600)
    minutes, secs = divmod(rem, 60)
    if hours:
        return f"{hours}:{minutes:02d}:{secs:02d}"
    return f"{minutes}:{secs:02d}"


def slugify(text: str) -> str:
    """'Agujero Negro' -> 'agujero_negro' (safe for a filename)."""
    slug = re.sub(r"[^a-z0-9]+", "_", normalize(text)).strip("_")
    return slug or "search"


def print_results(hits: list[SearchHit]) -> None:
    print(f"\nFound {len(hits)} fragment(s):\n")
    print(f"  {'#':>3}  {'date':10}  {'start-end':>15}  {'dur':>6}  {'rel':>4}  topic")
    print(f"  {'-'*3}  {'-'*10}  {'-'*15}  {'-'*6}  {'-'*4}  {'-'*40}")
    for index, hit in enumerate(hits, 1):
        span = f"{format_hms(hit.topic.start)}-{format_hms(hit.topic.end)}"
        dur = format_hms(hit.topic.duration)
        rel = f"{round(hit.score * 100):>3}%" if hit.score is not None else "   -"
        print(
            f"  {index:>3}  {hit.date:%Y-%m-%d}  {span:>15}  {dur:>6}  {rel:>4}  "
            f"{hit.topic.name[:60]}"
        )
        if hit.reason:  # only present when the LLM classifier ran
            print(f"  {'':>3}  {'':>10}  {'':>15}  {'':>6}  {'':>4}  · {hit.reason[:70]}")


def format_chat_answer(answer: RagAnswer) -> str:
    """Render a grounded answer plus a one-line citation of the episodes used.

    Passages from the same episode are cited once, in first-seen order, so the
    line stays short even when several chunks of one fragment were retrieved.
    """
    lines = [answer.text]
    episodes: list[str] = []
    for passage in answer.sources:
        label = f"ep{passage.episode} ({passage.topic})"
        if label not in episodes:
            episodes.append(label)
    if episodes:
        lines.append("Sources: " + ", ".join(episodes))
    return "\n".join(lines)


def run_chat_repl(answerer, *, read=input, write=print) -> None:
    """Interactive question/answer loop over an open RAG session.

    ``read``/``write`` are injected so the loop is testable without a terminal.
    An empty line, ``exit``/``quit`` or EOF/Ctrl-C ends the session.
    """
    write("Chat ready. Ask about the selected fragments "
          "(empty line or 'exit' to quit).")
    while True:
        try:
            question = read("> ").strip()
        except (EOFError, KeyboardInterrupt):
            write("")
            break
        if not question or question.lower() in ("exit", "quit"):
            break
        write(format_chat_answer(answerer.answer(question)))


def confirm(prompt: str) -> bool:
    try:
        answer = input(f"{prompt} [y/N]: ").strip().lower()
    except (EOFError, KeyboardInterrupt):
        print()
        return False
    return answer in ("y", "yes", "s", "si", "sí")


def total_duration(hits: list[SearchHit]) -> int:
    """Sum of known durations (final topics without an 'end' do not count)."""
    return sum(hit.topic.duration or 0 for hit in hits)


def _report(message: str) -> None:
    """Reporter passed to the assembler; '\\r'-prefixed messages stay inline."""
    if message.startswith("\r"):
        print(message, end="", flush=True)
    else:
        print(message)


# --- argument parsing -----------------------------------------------------

def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Generate an MP3 with the fragments of a topic from the "
        "podcast 'Coffee Break: Señal y Ruido'."
    )
    parser.add_argument("query", nargs="?", help="term to search for")
    parser.add_argument("--semantic", action="store_true",
                        help="use AI semantic search (embeddings) instead of "
                             "keyword matching")
    parser.add_argument("--model", default="local", metavar="PROVIDER",
                        help="embedding provider for --semantic: 'local' "
                             "(default, free) or 'gemini' (needs GEMINI_API_KEY)")
    parser.add_argument("--classify", action="store_true",
                        help="with --semantic, let an LLM judge each candidate's "
                             "relevance (needs GEMINI_API_KEY)")
    parser.add_argument("--top-k", type=int, metavar="N",
                        help="with --semantic, keep at most N candidates "
                             "(default from settings)")
    parser.add_argument("--threshold", type=float, metavar="T",
                        help="with --semantic, minimum similarity 0..1 to keep a "
                             "candidate (default from settings)")
    parser.add_argument("--refresh", action="store_true",
                        help="ignore the feed cache and download it again")
    parser.add_argument("--limit", type=int, metavar="N",
                        help="use at most the first N fragments")
    parser.add_argument("--yes", "-y", action="store_true",
                        help="do not ask for confirmation before generating")
    parser.add_argument("--keep-temp", action="store_true",
                        help="keep the temporary fragments")
    parser.add_argument("--no-intro", action="store_true",
                        help="do not add the announcement (episode and date) "
                             "before each fragment")
    parser.add_argument("--no-disclaimer", action="store_true",
                        help="do not add the spoken educational disclaimer at the start")
    parser.add_argument("--split", type=int, metavar="MIN",
                        help="split the output into blocks of at most MIN minutes "
                             "(grouping whole fragments)")
    parser.add_argument("--transcript", action="store_true",
                        help="transcribe the generated audio to .txt and .srt "
                             "(faster-whisper)")
    parser.add_argument("--chat", action="store_true",
                        help="instead of building audio, open an interactive Q&A "
                             "(RAG) over the found fragments (needs GEMINI_API_KEY)")
    parser.add_argument("--book", action="store_true",
                        help="instead of building audio, compose a didactic "
                             "Markdown book (+ PDF/EPUB via pandoc) over the "
                             "found fragments (needs GEMINI_API_KEY)")
    parser.add_argument("--output", type=Path, metavar="PATH",
                        help="output MP3 path (default output/<term>_<date>.mp3)")
    parser.add_argument("--clean-cache", action="store_true",
                        help="delete the cache (feed + episodes) and exit")
    parser.add_argument("--email", nargs="?", const="", metavar="ADDR",
                        help="send the MP3 by e-mail (to ADDR, or to COFFEE_MAIL_TO/"
                             "sender if omitted). Requires COFFEE_SMTP_USER/PASS")
    return parser.parse_args(argv)


# --- entry point ----------------------------------------------------------

def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    settings = Settings.from_env()

    try:
        search_service = build_search_service(settings, args)
    except CoffeeError as error:
        print(f"Error: {error}", file=sys.stderr)
        return 1
    service, cache = build_service(settings, search_service)

    if args.clean_cache:
        files, size = cache.clear()
        print(f"Cache cleared: {files} file(s), {size / (1024*1024):.1f} MB freed.")
        return 0

    query = args.query or input("Topic to search: ").strip()
    if not query:
        print("No term was given.", file=sys.stderr)
        return 1

    try:
        mode = "semantic" if args.semantic else "keyword"
        print("Loading feed..." + (" (forcing download)" if args.refresh else ""))
        episodes = service.load_episodes(force_refresh=args.refresh)
        print(f"  {len(episodes)} episodes with topics.")

        print(f"Searching ({mode})...")
        hits = service.search(episodes, query)
        if not hits:
            print(f"\nNo results for '{query}'.")
            return 0
        if args.limit:
            hits = hits[: args.limit]

        print_results(hits)

        if args.chat:
            print("\nOpening chat over these fragments "
                  "(transcribing as needed; this may take a while)...")
            rag = build_rag_service(settings, model=args.model)
            answerer = rag.open_session([hit.fragment for hit in hits])
            run_chat_repl(answerer)
            return 0

        if args.book:
            print("\nComposing the book over these fragments "
                  "(transcribing as needed; this may take a while)...")
            composer = build_book_composer(settings, model=args.model)
            book = composer.compose([hit.fragment for hit in hits], query)
            out_path = args.output or (
                settings.output_dir / f"{slugify(query)}_{datetime.now():%Y-%m-%d}.md"
            )
            out_path.parent.mkdir(parents=True, exist_ok=True)
            out_path.write_text(MarkdownRenderer().render(book), encoding="utf-8")
            print(f"OK {out_path}")
            for dest, fmt in PandocExporter().export(out_path, ["pdf", "epub"], report=_report):
                print(f"   {fmt}: {dest}")
            return 0

        minutes = total_duration(hits) // 60
        episode_count = len({hit.episode.guid for hit in hits})
        print(f"\nApproximate total duration: ~{minutes} min across "
              f"{episode_count} episode(s).")
        if not args.yes:
            if len(hits) > settings.many_results_warning:
                print(f"! There are {len(hits)} fragments; this may take a "
                      "while and use a fair amount of space.")
            if not confirm("Generate the concatenated audio?"):
                print("Cancelled.")
                return 0

        out_path = args.output or (
            settings.output_dir / f"{slugify(query)}_{datetime.now():%Y-%m-%d}.mp3"
        )
        outputs = service.build_clips(
            [hit.fragment for hit in hits],
            out_path,
            keep_temp=args.keep_temp,
            intro=not args.no_intro,
            disclaimer=not args.no_disclaimer,
            split_seconds=args.split * 60 if args.split else None,
            report=_report,
        )

        print()
        for path in outputs:
            size_mb = path.stat().st_size / (1024 * 1024)
            print(f"OK {path}  ({size_mb:.1f} MB)")

        if args.transcript:
            print("\nTranscribing (faster-whisper)... this may take a while.")
            for path in outputs:
                try:
                    written = service.transcribe(path)
                    for kind, dest in written.items():
                        print(f"   {kind}: {dest}")
                except CoffeeError as error:
                    print(f"! Could not transcribe {path.name}: {error}",
                          file=sys.stderr)

        if args.email is not None:
            recipient = args.email or None  # empty string -> use the default value
            subject = f"Coffee Break: fragments about '{query}'"
            print("\nSending by e-mail...")
            for path in outputs:
                body = (
                    f"Attached is '{path.name}' from the podcast 'Coffee Break: "
                    f"Señal y Ruido' about '{query}'.\n\nGenerated automatically."
                )
                try:
                    to = service.send_email(path, subject, body, recipient)
                    print(f"   {path.name} -> {to}")
                except MailError as error:
                    # The MP3 is already generated; an e-mail failure does not
                    # invalidate the work.
                    print(f"! Could not send {path.name}: {error}", file=sys.stderr)
                    return 2
        return 0

    except CoffeeError as error:
        print(f"\nError: {error}", file=sys.stderr)
        return 1
    except KeyboardInterrupt:
        print("\nInterrupted.", file=sys.stderr)
        return 130
