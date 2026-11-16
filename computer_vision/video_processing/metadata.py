"""Video metadata extraction."""
from dataclasses import dataclass
import cv2
from .video_loader import validate_video_path


@dataclass(frozen=True)
class VideoMetadata:
    fps: float
    frame_count: int
    width: int
    height: int


def read_video_metadata(path: str) -> VideoMetadata:
    """Read basic metadata without decoding the entire video."""
    video = cv2.VideoCapture(str(validate_video_path(path)))
    if not video.isOpened():
        raise ValueError(f"Unable to open video: {path}")
    try:
        metadata = VideoMetadata(video.get(cv2.CAP_PROP_FPS), int(video.get(cv2.CAP_PROP_FRAME_COUNT)), int(video.get(cv2.CAP_PROP_FRAME_WIDTH)), int(video.get(cv2.CAP_PROP_FRAME_HEIGHT)))
        if metadata.fps <= 0 or metadata.width <= 0 or metadata.height <= 0:
            raise ValueError(f"Video metadata is invalid: {path}")
        return metadata
    finally:
        video.release()
