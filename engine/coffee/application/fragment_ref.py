"""Stable, human-readable fragment identifiers for the JSON contract.

A fragment id has the form ``ep<key>@<start>-<end>`` (e.g. ``ep237@2340-2880``;
an open-ended last topic is ``ep237@5910-``). The key is the episode number,
plus the lowercase side letter for part episodes (``Ep563_B`` -> ``ep563b``);
episodes without a number fall back to a stable digest of the feed guid
(``epx3fa2c81@...``), so no two episodes ever share a key. The id is what the
API sends back in a ``generate`` selection, so it must round-trip: `to_id`
builds it from a ``Fragment``, and `build_index` maps every catalogue fragment
back by id.

Centralised here because two layers depend on the exact same format: search
(emits ids) and generate (resolves them).
"""

from __future__ import annotations

import hashlib

from coffee.domain.errors import CoffeeError
from coffee.domain.models import Episode, Fragment
from coffee.speech.announcements import episode_key


def _episode_id_key(episode: Episode) -> str:
    """Unique per-episode key: number(+side), or a guid digest when unnumbered."""
    key = episode_key(episode.title)
    if key:
        return key
    digest = hashlib.sha1(episode.guid.encode("utf-8")).hexdigest()[:8]
    return f"x{digest}"


def to_id(fragment: Fragment) -> str:
    """Build the contract id for a fragment: ``ep<key>@<start>-<end>``."""
    key = _episode_id_key(fragment.episode)
    end = fragment.topic.end
    return f"ep{key}@{fragment.topic.start}-{'' if end is None else end}"


def build_index(episodes: list[Episode]) -> dict[str, Fragment]:
    """Map every fragment in the catalogue by its id (first wins on collision)."""
    index: dict[str, Fragment] = {}
    for episode in episodes:
        for topic in episode.topics:
            fragment = Fragment(episode=episode, topic=topic)
            index.setdefault(to_id(fragment), fragment)
    return index


def resolve(episodes: list[Episode], ids: list[str]) -> list[Fragment]:
    """Resolve fragment ids to fragments; unknown ids raise (never shrink).

    Silently dropping an unknown id would let a typo in a ``generate``
    selection produce a shorter clip with no warning, so the caller gets the
    exact offending ids instead.
    """
    index = build_index(episodes)
    unknown = [fid for fid in ids if fid not in index]
    if unknown:
        raise CoffeeError(f"Unknown fragment id(s): {', '.join(unknown)}")
    return [index[fid] for fid in ids]
