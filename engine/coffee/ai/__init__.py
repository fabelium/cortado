"""AI layer: pluggable embedding and chat providers (local or API).

Two ports decouple the application from any concrete model:

* ``EmbeddingProvider`` — turns text into vectors (semantic search).
* ``ChatModel`` — answers a prompt (relevance classification today; RAG chat and
  book summaries tomorrow).

Concrete adapters (local ``fastembed`` / Ollama, or API ``gemini``) are selected
at the composition root through ``ProviderFactory``. The rest of the codebase
depends only on the ports, never on a vendor SDK.
"""
