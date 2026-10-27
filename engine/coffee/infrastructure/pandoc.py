"""Export a Markdown file to PDF/EPUB via pandoc (Adapter over an external CLI).

The pandoc invocation and the executable lookup are injected so the adapter is
testable without pandoc installed. Graceful degradation is the contract: if
pandoc is absent or a single conversion fails, it is reported and skipped — the
Markdown is already a valid result, so export never aborts the book.
"""

from __future__ import annotations

import shutil
import subprocess
from pathlib import Path
from typing import Callable

_EXTENSION = {"pdf": ".pdf", "epub": ".epub"}

# A hung pandoc must not hang the engine; a timeout degrades like any failure.
_TIMEOUT_SECONDS = 120


def _default_runner(command: list[str]) -> None:
    subprocess.run(command, check=True, timeout=_TIMEOUT_SECONDS)


class PandocExporter:
    """Converts Markdown to the requested formats, degrading gracefully."""

    def __init__(
        self,
        runner: Callable[[list[str]], None] | None = None,
        which: Callable[[str], str | None] = shutil.which,
    ) -> None:
        self._run = runner or _default_runner
        self._which = which

    def export(
        self,
        md_path: Path,
        formats: list[str],
        report: Callable[[str], None] = lambda _message: None,
    ) -> list[tuple[Path, str]]:
        if not self._which("pandoc"):
            report("! pandoc not found; only Markdown was produced.")
            return []
        produced: list[tuple[Path, str]] = []
        for fmt in formats:
            try:
                dest = Path(md_path).with_suffix(_EXTENSION[fmt])
                self._run(["pandoc", str(md_path), "-o", str(dest)])
                produced.append((dest, fmt))
            except Exception as error:  # one bad format must not sink the rest
                report(f"! pandoc failed for {fmt}: {error}")
        return produced
