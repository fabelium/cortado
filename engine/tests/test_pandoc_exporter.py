"""PandocExporter: convert a Markdown file to PDF/EPUB via pandoc, degrading
gracefully when pandoc is missing or a conversion fails. The pandoc runner and
the `which` lookup are injected. Run: python3 tests/test_pandoc_exporter.py
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from coffee.infrastructure.pandoc import PandocExporter


def test_exports_each_format_and_returns_outputs():
    commands = []
    exporter = PandocExporter(runner=commands.append, which=lambda _name: "/usr/bin/pandoc")

    outputs = exporter.export(Path("/out/marte.md"), ["pdf", "epub"])

    assert outputs == [(Path("/out/marte.pdf"), "pdf"), (Path("/out/marte.epub"), "epub")]
    assert commands[0][:1] == ["pandoc"]
    assert str(Path("/out/marte.pdf")) in commands[0]


def test_missing_pandoc_degrades_to_no_outputs():
    notes = []
    exporter = PandocExporter(runner=lambda _cmd: None, which=lambda _name: None)

    outputs = exporter.export(Path("/out/marte.md"), ["pdf"], report=notes.append)

    assert outputs == []
    assert any("pandoc" in note.lower() for note in notes)


def test_default_runner_enforces_a_timeout():
    from coffee.infrastructure import pandoc as pandoc_module

    seen = {}

    def fake_run(cmd, **kwargs):
        seen.update(kwargs)

    original = pandoc_module.subprocess.run
    pandoc_module.subprocess.run = fake_run
    try:
        pandoc_module._default_runner(["pandoc", "in.md", "-o", "out.pdf"])
    finally:
        pandoc_module.subprocess.run = original
    assert seen.get("timeout", 0) > 0  # a hung pandoc must not hang the engine
    assert seen["check"] is True


def test_one_failing_format_is_skipped_others_kept():
    def runner(cmd):
        if "marte.pdf" in " ".join(cmd):
            raise RuntimeError("boom")

    notes = []
    exporter = PandocExporter(runner=runner, which=lambda _name: "/usr/bin/pandoc")

    outputs = exporter.export(Path("/out/marte.md"), ["pdf", "epub"], report=notes.append)

    assert outputs == [(Path("/out/marte.epub"), "epub")]
    assert any("pdf" in note.lower() for note in notes)


if __name__ == "__main__":
    fns = [v for k, v in sorted(globals().items()) if k.startswith("test_")]
    for fn in fns:
        fn()
        print(f"  ok  {fn.__name__}")
    print(f"\n{len(fns)} tests OK")
