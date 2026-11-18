"""Metadata extraction using OpenCV with optional FFprobe enrichment."""
from pathlib import Path
import json
import shutil
import subprocess
import cv2


def _ratio(width: int | None, height: int | None) -> str | None:
    if not width or not height:
        return None
    from math import gcd
    divisor = gcd(width, height)
    return f"{width // divisor}:{height // divisor}"


def extract_metadata(path: Path) -> dict[str, object]:
    capture = cv2.VideoCapture(str(path))
    if not capture.isOpened():
        raise ValueError("Unable to open video for metadata extraction.")
    try:
        fps = float(capture.get(cv2.CAP_PROP_FPS)) or None
        frames = int(capture.get(cv2.CAP_PROP_FRAME_COUNT)) or None
        width = int(capture.get(cv2.CAP_PROP_FRAME_WIDTH)) or None
        height = int(capture.get(cv2.CAP_PROP_FRAME_HEIGHT)) or None
        duration = (frames / fps) if frames and fps and fps > 0 else None
        codec_code = int(capture.get(cv2.CAP_PROP_FOURCC))
        codec = "".join(chr((codec_code >> (8 * index)) & 0xFF) for index in range(4)).strip() or None
    finally:
        capture.release()
    ffprobe = shutil.which("ffprobe")
    if ffprobe:
        try:
            raw = subprocess.run([ffprobe, "-v", "error", "-select_streams", "v:0", "-show_entries", "stream=codec_name,duration,nb_frames", "-of", "json", str(path)], capture_output=True, text=True, timeout=10, check=True)
            stream = json.loads(raw.stdout).get("streams", [{}])[0]
            codec = stream.get("codec_name") or codec
            duration = float(stream["duration"]) if stream.get("duration") else duration
            frames = int(stream["nb_frames"]) if str(stream.get("nb_frames", "")).isdigit() else frames
        except (subprocess.SubprocessError, ValueError, KeyError, json.JSONDecodeError):
            pass
    return {"format": path.suffix.removeprefix(".").lower(), "duration_seconds": duration, "width": width, "height": height, "original_fps": fps, "total_frames": frames, "aspect_ratio": _ratio(width, height), "codec": codec}
