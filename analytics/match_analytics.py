"""No fake match statistics."""
from typing import Mapping, Sequence


def summarize_match(observations: Sequence[Mapping[str, object]], events: Sequence[Mapping[str, object]]) -> dict[str, int]:
    """Return transparent record counts, not inferred football statistics."""
    if not observations and not events:
        raise ValueError("Observations or event candidates are required")
    return {"observation_count": len(observations), "event_candidate_count": len(events)}
