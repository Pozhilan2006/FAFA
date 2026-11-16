"""Simple, input-dependent player motion calculations."""
from math import hypot
from typing import Sequence


def calculate_distance(positions: Sequence[tuple[float, float]]) -> float:
    """Calculate metres travelled from sequential calibrated pitch positions."""
    if len(positions) < 2:
        raise ValueError("At least two pitch positions are required")
    return sum(hypot(b[0] - a[0], b[1] - a[1]) for a, b in zip(positions, positions[1:]))


def calculate_speed(distance_metres: float, elapsed_seconds: float) -> float:
    """Calculate m/s from actual distance and elapsed time."""
    if distance_metres < 0:
        raise ValueError("distance_metres cannot be negative")
    if elapsed_seconds <= 0:
        raise ValueError("elapsed_seconds must be positive")
    return distance_metres / elapsed_seconds
