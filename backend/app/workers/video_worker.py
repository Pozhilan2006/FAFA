"""Lightweight database-backed background worker for a single processing job."""
from datetime import datetime
from pathlib import Path
import logging
from math import ceil
import cv2
from sqlalchemy import delete
from ..core.config import settings
from ..database.connection import SessionLocal
from ..database.models import ExtractedFrame, ProcessingJob, Video
from ..services.frame_extractor import extract_sampled_frames, frame_filename, preprocess_frame

logger = logging.getLogger(__name__)


def process_video(job_id: str) -> None:
    database = SessionLocal()
    try:
        job = database.get(ProcessingJob, job_id)
        if not job:
            return
        video = database.get(Video, job.video_id)
        if not video:
            raise ValueError("Video record no longer exists.")
        job.status, job.started_at = "processing", datetime.utcnow()
        if video.total_frames and video.original_fps:
            job.frames_expected = ceil((video.total_frames / video.original_fps) * job.sampling_fps)
        database.execute(delete(ExtractedFrame).where(ExtractedFrame.video_id == video.id))
        database.commit()
        original_directory = settings.storage_path / "frames" / video.id / "original"
        processed_directory = settings.storage_path / "frames" / video.id / "processed"
        original_directory.mkdir(parents=True, exist_ok=True)
        processed_directory.mkdir(parents=True, exist_ok=True)
        for number, timestamp, frame in extract_sampled_frames(Path(video.file_path), job.sampling_fps):
            try:
                name = frame_filename(number, timestamp)
                original_path = original_directory / name
                processed_path = processed_directory / name
                if not cv2.imwrite(str(original_path), frame):
                    raise ValueError("OpenCV could not write original frame.")
                preprocessed = preprocess_frame(frame, settings.max_frame_dimension)
                if not cv2.imwrite(str(processed_path), preprocessed, [cv2.IMWRITE_JPEG_QUALITY, 95]):
                    raise ValueError("OpenCV could not write processed frame.")
                height, width = frame.shape[:2]
                processed_height, processed_width = preprocessed.shape[:2]
                database.add(ExtractedFrame(video_id=video.id, frame_number=number, timestamp_seconds=timestamp, original_frame_path=str(original_path), processed_frame_path=str(processed_path), original_width=width, original_height=height, processed_width=processed_width, processed_height=processed_height))
                job.frames_processed += 1
            except Exception as exc:
                logger.warning("Frame %s failed for video %s: %s", number, video.id, exc)
                job.frames_failed += 1
            if (job.frames_processed + job.frames_failed) % 10 == 0:
                database.commit()
        job.status, job.completed_at = "completed", datetime.utcnow()
        database.commit()
    except Exception as exc:
        logger.exception("Video processing failed for job %s", job_id)
        database.rollback()
        job = database.get(ProcessingJob, job_id)
        if job:
            job.status, job.error_message, job.completed_at = "failed", str(exc), datetime.utcnow()
            database.commit()
    finally:
        database.close()
