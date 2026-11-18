"""Persistence models for video ingestion and object detection; files remain on local storage."""
from __future__ import annotations
from datetime import datetime
from uuid import uuid4
from sqlalchemy import DateTime, Float, ForeignKey, Integer, JSON, String, Text, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship
from .base import Base


def new_id() -> str:
    return uuid4().hex


class Video(Base):
    __tablename__ = "videos"
    id: Mapped[str] = mapped_column(String(32), primary_key=True, default=new_id)
    original_filename: Mapped[str] = mapped_column(String(255))
    stored_filename: Mapped[str] = mapped_column(String(255), unique=True)
    file_path: Mapped[str] = mapped_column(Text)
    file_size: Mapped[int] = mapped_column(Integer)
    format: Mapped[str] = mapped_column(String(16))
    duration_seconds: Mapped[float | None] = mapped_column(Float, nullable=True)
    width: Mapped[int | None] = mapped_column(Integer, nullable=True)
    height: Mapped[int | None] = mapped_column(Integer, nullable=True)
    original_fps: Mapped[float | None] = mapped_column(Float, nullable=True)
    total_frames: Mapped[int | None] = mapped_column(Integer, nullable=True)
    aspect_ratio: Mapped[str | None] = mapped_column(String(32), nullable=True)
    codec: Mapped[str | None] = mapped_column(String(64), nullable=True)
    upload_status: Mapped[str] = mapped_column(String(24), default="uploaded")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    jobs: Mapped[list[ProcessingJob]] = relationship(back_populates="video", cascade="all, delete-orphan")
    frames: Mapped[list[ExtractedFrame]] = relationship(back_populates="video", cascade="all, delete-orphan")
    detection_jobs: Mapped[list[DetectionJob]] = relationship(back_populates="video", cascade="all, delete-orphan")


class ProcessingJob(Base):
    __tablename__ = "processing_jobs"
    id: Mapped[str] = mapped_column(String(32), primary_key=True, default=new_id)
    video_id: Mapped[str] = mapped_column(ForeignKey("videos.id"), index=True)
    status: Mapped[str] = mapped_column(String(24), default="queued", index=True)
    sampling_fps: Mapped[float] = mapped_column(Float)
    frames_expected: Mapped[int | None] = mapped_column(Integer, nullable=True)
    frames_processed: Mapped[int] = mapped_column(Integer, default=0)
    frames_failed: Mapped[int] = mapped_column(Integer, default=0)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    started_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    video: Mapped[Video] = relationship(back_populates="jobs")


class ExtractedFrame(Base):
    __tablename__ = "extracted_frames"
    id: Mapped[str] = mapped_column(String(32), primary_key=True, default=new_id)
    video_id: Mapped[str] = mapped_column(ForeignKey("videos.id"), index=True)
    frame_number: Mapped[int] = mapped_column(Integer)
    timestamp_seconds: Mapped[float] = mapped_column(Float)
    original_frame_path: Mapped[str] = mapped_column(Text)
    processed_frame_path: Mapped[str | None] = mapped_column(Text, nullable=True)
    original_width: Mapped[int] = mapped_column(Integer)
    original_height: Mapped[int] = mapped_column(Integer)
    processed_width: Mapped[int] = mapped_column(Integer)
    processed_height: Mapped[int] = mapped_column(Integer)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    video: Mapped[Video] = relationship(back_populates="frames")


Index("ix_frame_video_number", ExtractedFrame.video_id, ExtractedFrame.frame_number, unique=True)


class DetectionJob(Base):
    __tablename__ = "detection_jobs"
    id: Mapped[str] = mapped_column(String(32), primary_key=True, default=new_id)
    video_id: Mapped[str] = mapped_column(ForeignKey("videos.id"), index=True)
    model_name: Mapped[str] = mapped_column(String(255))
    confidence_threshold: Mapped[float] = mapped_column(Float)
    batch_size: Mapped[int] = mapped_column(Integer)
    status: Mapped[str] = mapped_column(String(24), default="queued", index=True)
    total_frames: Mapped[int | None] = mapped_column(Integer, nullable=True)
    processed_frames: Mapped[int] = mapped_column(Integer, default=0)
    failed_frames: Mapped[int] = mapped_column(Integer, default=0)
    total_detections: Mapped[int] = mapped_column(Integer, default=0)
    processing_device: Mapped[str | None] = mapped_column(String(64), nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    started_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    video: Mapped[Video] = relationship(back_populates="detection_jobs")
    detections: Mapped[list[ObjectDetection]] = relationship(back_populates="job", cascade="all, delete-orphan")
    annotated_frames: Mapped[list[AnnotatedFrame]] = relationship(back_populates="job", cascade="all, delete-orphan")


class ObjectDetection(Base):
    __tablename__ = "object_detections"
    id: Mapped[str] = mapped_column(String(32), primary_key=True, default=new_id)
    detection_job_id: Mapped[str] = mapped_column(ForeignKey("detection_jobs.id"), index=True)
    video_id: Mapped[str] = mapped_column(ForeignKey("videos.id"), index=True)
    frame_id: Mapped[str] = mapped_column(ForeignKey("extracted_frames.id"), index=True)
    frame_number: Mapped[int] = mapped_column(Integer, index=True)
    timestamp_seconds: Mapped[float] = mapped_column(Float)
    class_id: Mapped[int] = mapped_column(Integer)
    class_name: Mapped[str] = mapped_column(String(64), index=True)
    confidence: Mapped[float] = mapped_column(Float)
    x_min: Mapped[float] = mapped_column(Float)
    y_min: Mapped[float] = mapped_column(Float)
    x_max: Mapped[float] = mapped_column(Float)
    y_max: Mapped[float] = mapped_column(Float)
    image_width: Mapped[int] = mapped_column(Integer)
    image_height: Mapped[int] = mapped_column(Integer)
    normalized_bbox: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    job: Mapped[DetectionJob] = relationship(back_populates="detections")


Index("ix_detection_job_frame", ObjectDetection.detection_job_id, ObjectDetection.frame_id)
Index("ix_detection_video_job", ObjectDetection.video_id, ObjectDetection.detection_job_id)


class AnnotatedFrame(Base):
    __tablename__ = "annotated_frames"
    id: Mapped[str] = mapped_column(String(32), primary_key=True, default=new_id)
    detection_job_id: Mapped[str] = mapped_column(ForeignKey("detection_jobs.id"), index=True)
    frame_id: Mapped[str] = mapped_column(ForeignKey("extracted_frames.id"), index=True)
    original_frame_path: Mapped[str] = mapped_column(Text)
    annotated_frame_path: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    job: Mapped[DetectionJob] = relationship(back_populates="annotated_frames")


Index("ix_annotated_job_frame", AnnotatedFrame.detection_job_id, AnnotatedFrame.frame_id, unique=True)
