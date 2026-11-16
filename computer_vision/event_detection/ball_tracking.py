"""Ball tracking contract."""
from typing import Protocol


class BallTracker(Protocol):
    def position_at(self, frame_number: int) -> tuple[float, float] | None: ...
