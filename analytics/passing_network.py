"""Passing network placeholder."""
from typing import Mapping, Sequence


def generate_passing_network(events: Sequence[Mapping[str, object]]) -> dict[tuple[str, str], int]:
    """Build edges only from candidate/confirmed pass records with track IDs."""
    edges: dict[tuple[str, str], int] = {}
    for event in events:
        if event.get("event_type") != "pass":
            continue
        source, target = event.get("source_track_id"), event.get("target_track_id")
        if not isinstance(source, str) or not isinstance(target, str):
            continue
        edges[(source, target)] = edges.get((source, target), 0) + 1
    return edges
