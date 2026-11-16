"""Coordinate transformation contract."""
from typing import Protocol


class PitchTransformer(Protocol):
    """Convert image pixels to pitch metres only after calibration."""
    def transform(self, image_position: tuple[float, float]) -> tuple[float, float] | None: ...
