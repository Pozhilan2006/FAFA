"""Public API contracts for ingestion and frame processing."""
from datetime import datetime
from pydantic import BaseModel, Field


class UploadResponse(BaseModel):
    video_id: str
    filename: str
    status: str
    message: str


class VideoMetadataResponse(BaseModel):
    video_id: str
    original_filename: str
    file_size: int
    format: str
    duration_seconds: float | None
    width: int | None
    height: int | None
    resolution: str | None
    fps: float | None
    total_frames: int | None
    aspect_ratio: str | None
    codec: str | None
    status: str
    created_at: datetime


class ProcessRequest(BaseModel):
    sampling_fps: float = Field(default=2, gt=0, le=30)
    force: bool = False


class ProcessingStatusResponse(BaseModel):
    job_id: str
    video_id: str
    status: str
    sampling_fps: float
    frames_expected: int | None
    frames_processed: int
    frames_failed: int
    progress_percentage: float | None
    error_message: str | None
    started_at: datetime | None
    completed_at: datetime | None


class FrameResponse(BaseModel):
    frame_id: str
    video_id: str
    frame_number: int
    timestamp_seconds: float
    original_width: int
    original_height: int
    processed_width: int
    processed_height: int
    image_url: str


class FramePage(BaseModel):
    items: list[FrameResponse]
    offset: int
    limit: int
    total: int
