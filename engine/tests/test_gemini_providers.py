"""Gemini adapters: the API key travels in the x-goog-api-key header, never in
the URL query string (query strings end up in proxy/server logs).
Run: python3 tests/test_gemini_providers.py
"""

import sys
from pathlib import Path
from types import SimpleNamespace

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from coffee.ai import gemini_chat, gemini_embedding
from coffee.ai.gemini_chat import GeminiChatModel
from coffee.ai.gemini_embedding import GeminiEmbeddingProvider


def _fake_response(payload):
    return SimpleNamespace(raise_for_status=lambda: None, json=lambda: payload)


def _with_fake_post(module, payload, fn):
    """Call ``fn`` with requests.post patched in ``module``; return seen kwargs."""
    seen = {}

    def fake_post(url, **kwargs):
        seen["url"] = url
        seen.update(kwargs)
        return _fake_response(payload)

    original = module.requests.post
    module.requests.post = fake_post
    try:
        fn()
    finally:
        module.requests.post = original
    return seen


def _assert_key_only_in_header(seen, key):
    assert seen.get("headers", {}).get("x-goog-api-key") == key
    assert key not in seen["url"]
    assert key not in str(seen.get("params") or "")


def test_chat_sends_the_key_in_a_header_not_the_url():
    payload = {"candidates": [{"content": {"parts": [{"text": "hola"}]}}]}
    model = GeminiChatModel(api_key="sekret-key")
    seen = _with_fake_post(gemini_chat, payload, lambda: model.complete("hola?"))
    _assert_key_only_in_header(seen, "sekret-key")


def test_embedding_sends_the_key_in_a_header_not_the_url():
    payload = {"embedding": {"values": [0.1, 0.2]}}
    provider = GeminiEmbeddingProvider(api_key="sekret-key")
    seen = _with_fake_post(
        gemini_embedding, payload, lambda: provider.embed_query("marte")
    )
    _assert_key_only_in_header(seen, "sekret-key")


if __name__ == "__main__":
    fns = [v for k, v in sorted(globals().items()) if k.startswith("test_")]
    for fn in fns:
        fn()
        print(f"  ok  {fn.__name__}")
    print(f"\n{len(fns)} tests OK")
