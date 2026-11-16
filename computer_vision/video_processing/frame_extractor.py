"""Frame extraction using OpenCV."""
from typing import Iterator
import cv2
import numpy as np
from .video_loader import validate_video_path


def iter_frames(path: str, start_frame: int = 0) -> Iterator[tuple[int, np.ndarray]]:
    """Yield numbered BGR frames from a validated video."""
    if start_frame < 0:
        raise ValueError("start_frame must be non-negative")
    capture = cv2.VideoCapture(str(validate_video_path(path)))
    if not capture.isOpened():
        raise ValueError(f"Unable to open video: {path}")
    capture.set(cv2.CAP_PROP_POS_FRAMES, start_frame)
    index = start_frame
    try:
        while True:
            ok, frame = capture.read()
            if not ok:
                break
            yield index, frame
            index += 1
    finally:
        capture.release()
