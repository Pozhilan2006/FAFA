"""Pydantic schemas for object detection API."""
from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field, model_validator


class DetectionStartRequest(BaseModel):
    confidence_threshold: float = Field(default=0.35, ge=0.0, le=1.0)
    batch_size: int = Field(default=8, ge=1, le=64)
    max_frames: int | None = Field(default=100, ge=1)
    process_all_frames: bool = False

    @model_validator(mode="after")
    def validate_scope(self) -> "DetectionStartRequest":
        if not self.process_all_frames and self.max_frames is None:
            raise ValueError("max_frames is required when process_all_frames is false.")
        return self


class DetectionJobResponse(BaseModel):
    job_id: str
    video_id: str
    status: str
    model_name: str
    confidence_threshold: float
    batch_size: int
    total_frames: int | None
    processed_frames: int
    failed_frames: int
    total_detections: int
    processing_device: str | None
    progress_percentage: float
    processing_duration_seconds: float | None
    error_message: str | None
    started_at: datetime | None
    completed_at: datetime | None


class DetectionSummaryResponse(BaseModel):
    job_id: str
    video_id: str
    total_person_detections: int
    total_sports_ball_detections: int
    total_detections: int
    frames_processed: int
    frames_with_detections: int
    frames_without_detections: int
    failed_frames: int
    average_confidence: float | None
    inference_seconds: float | None
    average_inference_seconds_per_frame: float | None
    frames_per_second: float | None


class BBox(BaseModel):
    x_min: float
    y_min: float
    x_max: float
    y_max: float


class NormalizedBBox(BaseModel):
    x_center: float
    y_center: float
    width: float
    height: float


class DetectionRecord(BaseModel):
    detection_id: str
    video_id: str
    frame_id: str
    frame_number: int
    timestamp_seconds: float
    class_id: int
    class_name: str
    confidence: float
    bbox: BBox
    image_width: int
    image_height: int
    normalized_bbox: NormalizedBBox | None = None


class DetectionFrameResult(BaseModel):
    frame_id: str
    frame_number: int
    timestamp_seconds: float
    original_image_url: str
    annotated_image_url: str | None
    detection_count: int
    detected_class_names: list[str]
    detections: list[DetectionRecord]


class DetectionResultsPage(BaseModel):
    items: list[DetectionFrameResult]
    offset: int
    limit: int
    total: int


class ModelInfoResponse(BaseModel):
    model_name: str
    model_path: str | None
    device: str
    loaded: bool
    class_names: dict[int, str] | None = None
    supported_target_classes: list[str]
    confidence_default: float
    batch_size_default: int
    detail: str | None = None
