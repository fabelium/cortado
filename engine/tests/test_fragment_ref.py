"""Fragment ids must be unique per fragment: part episodes (Ep563_A/Ep563_B)
keep their side letter and unnumbered episodes get a stable per-episode key,
so no two fragments from different episodes ever share an id.
Run: python3 tests/test_fragment_ref.py
"""

import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from coffee.application.fragment_ref import build_index, resolve, to_id
from coffee.domain.errors import CoffeeError
from coffee.domain.models import Episode, Fragment, TimeRange, Topic
from coffee.speech.announcements import episode_key


def _episode(guid, title, start=0, end=100):
    topic = Topic(name="tema", time_range=TimeRange(start=start, end=end))
    return Episode(guid, title, datetime(2019, 10, 17), "http://audio", (topic,))


def _fragment(episode):
    return Fragment(episode=episode, topic=episode.topics[0])


def test_episode_key_keeps_the_part_suffix():
    assert episode_key("Ep563_A: Antihidrógeno") == "563a"
    assert episode_key("Ep563_B: Antihidrógeno") == "563b"
    assert episode_key("Ep237: Insight en Marte") == "237"
    assert episode_key("Bonus: entrevista") == ""


def test_plain_numbered_id_is_unchanged():
    fragment = _fragment(_episode("guid", "Ep237: Insight en Marte", 300, 480))
    assert to_id(fragment) == "ep237@300-480"


def test_part_episodes_get_distinct_ids():
    part_a = _fragment(_episode("guid-a", "Ep563_A: x"))
    part_b = _fragment(_episode("guid-b", "Ep563_B: x"))
    assert to_id(part_a) == "ep563a@0-100"
    assert to_id(part_b) == "ep563b@0-100"


def test_unnumbered_episodes_get_distinct_stable_ids():
    bonus = _fragment(_episode("guid-bonus", "Bonus: entrevista"))
    special = _fragment(_episode("guid-especial", "Especial: directo"))
    assert to_id(bonus) != to_id(special)  # was: both collapsed to ep0@...
    assert to_id(bonus) == to_id(bonus)  # deterministic (must round-trip)
    assert to_id(bonus).startswith("ep")  # ids keep the ep prefix contract
    assert "@0-100" in to_id(bonus)


def test_resolve_rejects_unknown_ids_instead_of_dropping_them():
    episode = _episode("guid-a", "Ep563_A: x")
    known = to_id(_fragment(episode))
    try:
        resolve([episode], [known, "ep999@0-1"])
    except CoffeeError as error:
        assert "ep999@0-1" in str(error)  # the caller learns exactly what failed
    else:
        raise AssertionError("an unknown id must raise, not shrink the result")


def test_colliding_fragments_are_all_reachable():
    part_a = _episode("guid-a", "Ep563_A: x")
    part_b = _episode("guid-b", "Ep563_B: x")
    index = build_index([part_a, part_b])
    assert len(index) == 2  # was: first-wins left one part unreachable
    resolved = resolve([part_a, part_b], [to_id(_fragment(part_b))])
    assert resolved[0].episode is part_b


if __name__ == "__main__":
    fns = [v for k, v in sorted(globals().items()) if k.startswith("test_")]
    for fn in fns:
        fn()
        print(f"  ok  {fn.__name__}")
    print(f"\n{len(fns)} tests OK")
