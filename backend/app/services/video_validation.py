"""Streaming upload and decoder validation utilities."""
from pathlib import Path
from uuid import uuid4
import cv2
from fastapi import HTTPException, UploadFile, status

ALLOWED_EXTENSIONS = {".mp4", ".mov", ".avi"}


def safe_upload_name(filename: str | None) -> tuple[str, str]:
    """Return a display name and safe generated storage filename."""
    original = Path(filename or "upload").name
    extension = Path(original).suffix.lower()
    if extension not in ALLOWED_EXTENSIONS:
        raise HTTPException(status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE, detail="Only MP4, MOV, and AVI videos are supported.")
    return original, f"{uuid4().hex}{extension}"


async def save_upload(upload: UploadFile, destination: Path, max_bytes: int) -> int:
    """Copy an upload in chunks, rejecting files that exceed the configured limit."""
    destination.parent.mkdir(parents=True, exist_ok=True)
    size = 0
    try:
        with destination.open("xb") as target:
            while chunk := await upload.read(1024 * 1024):
                size += len(chunk)
                if size > max_bytes:
                    raise HTTPException(status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE, detail="Video exceeds the configured upload size limit.")
                target.write(chunk)
    except Exception:
        destination.unlink(missing_ok=True)
        raise
    finally:
        await upload.close()
    return size


def validate_decodable_video(path: Path) -> None:
    """Check container content by opening and decoding at least one frame."""
    capture = cv2.VideoCapture(str(path))
    try:
        if not capture.isOpened():
            raise ValueError("The file is not a readable video container.")
        ok, frame = capture.read()
        if not ok or frame is None or frame.size == 0:
            raise ValueError("The video cannot be decoded or contains no readable frames.")
    finally:
        capture.release()
