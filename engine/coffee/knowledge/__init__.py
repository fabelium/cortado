"""Knowledge layer: turn fragment audio into reusable, searchable text.

The cornerstone is the per-fragment transcript (cached forever), on top of which
later steps build passage chunking, a vector index and RAG chat/book features.
This is where the project's "transcribe on demand, never twice" strategy lives.
"""
