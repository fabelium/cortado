"""Tuning options (top_k / threshold) flow from the contract and CLI into the
semantic strategy. Written test-first. Run: python3 tests/test_search_tuning.py
"""

import json
import sys
from pathlib import Path
from types import SimpleNamespace

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import jsonschema

import engine
from coffee.cli import build_search_service
from coffee.config import Settings

_CONTRACT = Path(__file__).resolve().parent.parent.parent / "contract"


def _request_schema():
    return json.loads((_CONTRACT / "schema" / "request.schema.json").read_text("utf-8"))


def test_request_schema_accepts_top_k_and_threshold():
    request = {"version": "1.0", "action": "search", "query": "x",
               "options": {"top_k": 5, "threshold": 0.4}}
    jsonschema.validate(request, _request_schema())  # must not raise


def test_engine_namespace_includes_tuning():
    namespace = engine._search_namespace({"top_k": 9, "threshold": 0.2})
    assert namespace.top_k == 9
    assert namespace.threshold == 0.2


def test_build_search_service_honours_tuning():
    args = SimpleNamespace(semantic=True, model="local", classify=False,
                           top_k=7, threshold=0.55)
    service = build_search_service(Settings(), args)
    strategy = service._strategy
    assert strategy._top_k == 7
    assert strategy._threshold == 0.55


def test_tuning_falls_back_to_settings_defaults():
    settings = Settings()
    args = SimpleNamespace(semantic=True, model="local", classify=False,
                           top_k=None, threshold=None)
    strategy = build_search_service(settings, args)._strategy
    assert strategy._top_k == settings.semantic_top_k
    assert strategy._threshold == settings.semantic_threshold


def test_cli_parses_top_k_and_threshold_flags():
    from coffee.cli import parse_args

    args = parse_args(["x", "--semantic", "--top-k", "8", "--threshold", "0.45"])
    assert args.top_k == 8
    assert args.threshold == 0.45


def test_cli_top_k_threshold_default_to_none():
    from coffee.cli import parse_args

    args = parse_args(["x", "--semantic"])
    assert args.top_k is None
    assert args.threshold is None


if __name__ == "__main__":
    fns = [v for k, v in sorted(globals().items()) if k.startswith("test_")]
    for fn in fns:
        fn()
        print(f"  ok  {fn.__name__}")
    print(f"\n{len(fns)} tests OK")
