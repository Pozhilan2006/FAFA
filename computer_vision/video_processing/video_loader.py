"""Safe video-path validation."""
from pathlib import Path


def validate_video_path(path: str | Path) -> Path:
    """Return an existing video file path or raise a meaningful error."""
    candidate = Path(path)
    if not candidate.is_file():
        raise FileNotFoundError(f"Video file does not exist: {candidate}")
    if candidate.suffix.lower() not in {".mp4", ".avi", ".mov", ".mkv", ".webm"}:
        raise ValueError(f"Unsupported video extension: {candidate.suffix}")
    return candidate
