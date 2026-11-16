"""Candidate event contract."""
from typing import Protocol


class EventDetector(Protocol):
    """Events produced here are candidates, not confirmed football actions."""
    def detect_candidates(self, match_id: str) -> list[dict[str, object]]: ...
