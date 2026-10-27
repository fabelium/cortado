"""Security hardening of the JSON engine entry point. Written test-first.

Covers: path-traversal containment for transcribe sources, a defensive cap on
selection size, and generic (non-leaking) messages for unexpected errors.
Run: python3 tests/test_engine_security.py
"""

import contextlib
import io
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import jsonschema

import engine
from coffee.config import Settings
from coffee.domain.errors import CoffeeError


# --- path containment (pure helper) --------------------------------------

def test_safe_source_path_allows_inside_output():
    settings = Settings()
    path = engine._safe_source_path("output/clip.mp3", settings)
    assert path == (settings.output_dir / "clip.mp3").resolve()


def test_safe_source_path_rejects_relative_traversal():
    try:
        engine._safe_source_path("../../etc/passwd", Settings())
    except CoffeeError as error:
        assert "outside" in str(error).lower() or "allowed" in str(error).lower()
    else:
        raise AssertionError("traversal path must be rejected")


def test_safe_source_path_rejects_absolute_outside():
    try:
        engine._safe_source_path("/etc/passwd", Settings())
    except CoffeeError:
        pass
    else:
        raise AssertionError("absolute path outside output_dir must be rejected")


# --- selection size cap ---------------------------------------------------

def test_oversized_selection_is_rejected():
    huge = [f"ep{i}@0-1" for i in range(Settings().max_selection + 1)]
    try:
        engine.handle({"version": "1.0", "action": "generate",
                       "query": "x", "selection": huge})
    except CoffeeError as error:
        assert "many" in str(error).lower() or "máx" in str(error).lower() \
            or "max" in str(error).lower()
    else:
        raise AssertionError("an oversized selection must be rejected")


# --- generic error messages ----------------------------------------------

def _run_main(payload: str) -> dict:
    """Drive main() with a stdin payload, capturing the JSON it writes."""
    real_stdin = sys.stdin
    sys.stdin = io.StringIO(payload)
    out = io.StringIO()
    try:
        with contextlib.redirect_stdout(out):
            engine.main()
    finally:
        sys.stdin = real_stdin
    return json.loads(out.getvalue())


def test_unexpected_error_message_is_generic(monkeypatch=None):
    secret = "TOP SECRET internal path /srv/private"

    def boom(_request, _settings):
        raise RuntimeError(secret)

    original = engine._HANDLERS.get("search")
    engine._HANDLERS["search"] = boom
    try:
        response = _run_main('{"version":"1.0","action":"search","query":"x"}')
    finally:
        engine._HANDLERS["search"] = original

    assert response["ok"] is False
    assert response["code"] == 1
    assert secret not in response["error"]  # internal detail must NOT leak


def test_validation_error_still_informative():
    response = _run_main('{"version":"0.9","action":"search"}')
    assert response["ok"] is False
    assert "invalid request" in response["error"].lower()


if __name__ == "__main__":
    fns = [v for k, v in sorted(globals().items()) if k.startswith("test_")]
    for fn in fns:
        fn()
        print(f"  ok  {fn.__name__}")
    print(f"\n{len(fns)} tests OK")
