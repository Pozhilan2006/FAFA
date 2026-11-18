"""Incremental extraction and preprocessing; never holds an entire video in memory."""
from pathlib import Path
import cv2
import numpy as np


def preprocess_frame(frame: np.ndarray, max_dimension: int) -> np.ndarray:
    """Convert to BGR and downscale only when necessary, preserving aspect ratio."""
    if frame is None or frame.size == 0:
        raise ValueError("Frame is empty or unreadable.")
    if frame.ndim == 2:
        frame = cv2.cvtColor(frame, cv2.COLOR_GRAY2BGR)
    height, width = frame.shape[:2]
    scale = min(1.0, max_dimension / max(width, height))
    if scale < 1:
        frame = cv2.resize(frame, (round(width * scale), round(height * scale)), interpolation=cv2.INTER_AREA)
    return frame


def frame_filename(frame_number: int, timestamp_seconds: float) -> str:
    return f"frame_{frame_number:06d}_{timestamp_seconds:010.3f}.jpg"


def extract_sampled_frames(video_path: Path, sampling_fps: float):
    """Yield original frame index, timeline timestamp, and one decoded frame at a time."""
    capture = cv2.VideoCapture(str(video_path))
    if not capture.isOpened():
        raise ValueError("Unable to open video for frame extraction.")
    try:
        source_fps = float(capture.get(cv2.CAP_PROP_FPS))
        if source_fps <= 0:
            raise ValueError("Video FPS is unavailable; cannot sample a reliable timeline.")
        next_timestamp = 0.0
        frame_number = 0
        while True:
            ok, frame = capture.read()
            if not ok:
                break
            timestamp = frame_number / source_fps
            if timestamp + 1e-9 >= next_timestamp:
                yield frame_number, timestamp, frame
                next_timestamp += 1 / sampling_fps
            frame_number += 1
    finally:
        capture.release()
