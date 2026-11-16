"""Pitch detection placeholder."""
import numpy as np


def find_pitch_markings(frame: np.ndarray) -> None:
    """Return calibration data in a future implementation."""
    if frame.size == 0:
        raise ValueError("frame must not be empty")
    # TODO: detect pitch lines and calculate calibration.
    return None
