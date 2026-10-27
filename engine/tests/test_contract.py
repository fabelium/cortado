"""Validate the JSON contract examples against their schemas.

The contract lives in ../contract (repo level), shared by the Python engine and
the Laravel API. Every file in ``examples/`` is discovered by glob — a new
example can never go silently unvalidated — and mapped to its schema by name:
``*.request.json`` -> ``request.schema.json``; anything else takes its leading
token, ``<action>[.<variant>].response.json`` -> ``response.<action>.schema.json``.

Run: python3 -m pytest tests/test_contract.py -q
or directly: python3 tests/test_contract.py
"""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import jsonschema

_CONTRACT = Path(__file__).resolve().parent.parent.parent / "contract"
_SCHEMA = _CONTRACT / "schema"
_EXAMPLES = _CONTRACT / "examples"

# Every action must keep at least a request and a response example on disk.
_CORE_EXAMPLES = {
    "search.request.json", "search.response.json",
    "generate.request.json", "generate.response.json",
    "transcribe.request.json", "transcribe.response.json",
    "chat.request.json", "chat.response.json",
    "book.request.json", "book.response.json",
    "error.response.json",
}


def _load(path):
    return json.loads(path.read_text(encoding="utf-8"))


def _schema_path(example: Path) -> Path:
    if example.name.endswith(".request.json"):
        return _SCHEMA / "request.schema.json"
    action = example.name.split(".")[0]
    return _SCHEMA / f"response.{action}.schema.json"


def test_every_example_file_matches_its_schema():
    examples = sorted(_EXAMPLES.glob("*.json"))
    names = {example.name for example in examples}
    assert _CORE_EXAMPLES <= names, f"missing examples: {_CORE_EXAMPLES - names}"
    for example in examples:
        schema_path = _schema_path(example)
        assert schema_path.exists(), (
            f"{example.name} maps to no schema ({schema_path.name}); "
            "follow <action>[.<variant>].request|response.json"
        )
        try:
            jsonschema.validate(_load(example), _load(schema_path))
        except jsonschema.ValidationError as error:
            raise AssertionError(
                f"{example.name} violates {schema_path.name}: {error.message}"
            ) from error


if __name__ == "__main__":
    test_every_example_file_matches_its_schema()
    print("contract OK")
