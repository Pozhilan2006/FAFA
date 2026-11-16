"""Track trajectory structures."""
from dataclasses import dataclass


@dataclass(frozen=True)
class TrajectoryPoint:
    frame_number: int
    timestamp: float
    image_position: tuple[float, float]
