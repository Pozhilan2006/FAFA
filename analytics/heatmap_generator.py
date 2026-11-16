"""Heatmap placeholder."""
from typing import Sequence


def generate_player_heatmap(positions: Sequence[tuple[float, float]]) -> list[tuple[float, float]]:
    """Validate calibrated input; rasterisation is intentionally deferred."""
    if not positions:
        raise ValueError("Calibrated pitch positions are required")
    # TODO: bin validated positions into a pitch heatmap.
    return list(positions)
