"""Background worker for object detection jobs over extracted frames."""
from __future__ import annotations

import logging
from datetime import datetime
from pathlib import Path
from sqlalchemy import delete, func, select

from ..core.config import settings
from ..database.connection import SessionLocal
from ..database.models import AnnotatedFrame, DetectionJob, ExtractedFrame, ObjectDetection, Video
from ..services.detection.annotation import save_annotated_frame
from ..services.detection.inference import run_inference_on_frames
from ..services.detection import model_loader

logger = logging.getLogger(__name__)


def _cleanup_job_outputs(database, job_id: str, video_id: str) -> None:
    ann_rows = database.scalars(select(AnnotatedFrame).where(AnnotatedFrame.detection_job_id == job_id)).all()
    for row in ann_rows:
        try:
            Path(row.annotated_frame_path).unlink(missing_ok=True)
        except Exception:
            pass
    database.execute(delete(ObjectDetection).where(ObjectDetection.detection_job_id == job_id))
    database.execute(delete(AnnotatedFrame).where(AnnotatedFrame.detection_job_id == job_id))
    out_dir = settings.storage_path / "detections" / "annotated_frames" / video_id / job_id
    if out_dir.exists():
        try:
            for p in out_dir.glob("*"):
                try:
                    p.unlink(missing_ok=True)
                except Exception:
                    pass
            out_dir.rmdir()
        except Exception:
            pass


def process_detection(job_id: str, max_frames: int | None = None) -> None:
    database = SessionLocal()
    try:
        job = database.get(DetectionJob, job_id)
        if not job:
            return
        video = database.get(Video, job.video_id)
        if not video:
            raise ValueError("Video record no longer exists.")
        job.status = "processing"
        job.started_at = datetime.utcnow()
        job.error_message = None
        database.commit()

        # Avoid stale outputs on re-run/force with same job id semantics (fresh job used normally)
        _cleanup_job_outputs(database, job.id, video.id)
        database.commit()

        q = select(ExtractedFrame).where(ExtractedFrame.video_id == video.id).order_by(ExtractedFrame.frame_number)
        if max_frames is not None:
            q = q.limit(max_frames)
        frames = database.scalars(q).all()
        job.total_frames = len(frames)
        database.commit()
        if not frames:
            raise ValueError("No extracted frames found for this video. Run frame extraction before detection.")

        model, info = model_loader.load_model()
        job.model_name = info.model_name
        job.processing_device = info.device
        database.commit()

        annotated_dir = settings.storage_path / "detections" / "annotated_frames" / video.id / job.id
        annotated_dir.mkdir(parents=True, exist_ok=True)

        batch_size = max(1, int(job.batch_size))
        processed = 0
        failed = 0
        total_detections = 0
        # process incrementally in chunks to control memory and persist progress
        for start in range(0, len(frames), batch_size):
            chunk = frames[start : start + batch_size]
            result = run_inference_on_frames(
                model,
                chunk,
                confidence_threshold=float(job.confidence_threshold),
                batch_size=batch_size,
                device=info.device,
            )
            for item in result["results"]:
                frame = item["frame"]
                if item["error"]:
                    failed += 1
                    continue
                detections = item["detections"]
                image_path = Path(item["image_path"] or frame.processed_frame_path or frame.original_frame_path)
                annotated_path = annotated_dir / Path(image_path).name
                try:
                    save_annotated_frame(image_path, annotated_path, detections)
                    database.add(AnnotatedFrame(
                        detection_job_id=job.id,
                        frame_id=frame.id,
                        original_frame_path=str(image_path),
                        annotated_frame_path=str(annotated_path),
                    ))
                except Exception as exc:
                    logger.warning("Failed to annotate frame %s for job %s: %s", frame.id, job.id, exc)
                    failed += 1
                    continue
                for det in detections:
                    database.add(ObjectDetection(
                        detection_job_id=job.id,
                        video_id=video.id,
                        frame_id=frame.id,
                        frame_number=int(det["frame_number"]),
                        timestamp_seconds=float(det["timestamp_seconds"]),
                        class_id=int(det["class_id"]),
                        class_name=str(det["class_name"]),
                        confidence=float(det["confidence"]),
                        x_min=float(det["x_min"]),
                        y_min=float(det["y_min"]),
                        x_max=float(det["x_max"]),
                        y_max=float(det["y_max"]),
                        image_width=int(det["image_width"]),
                        image_height=int(det["image_height"]),
                        normalized_bbox=det.get("normalized_bbox"),
                    ))
                processed += 1
                total_detections += len(detections)
            job.processed_frames = processed
            job.failed_frames = failed
            job.total_detections = total_detections
            database.commit()

        job.status = "completed"
        job.completed_at = datetime.utcnow()
        job.processed_frames = processed
        job.failed_frames = failed
        job.total_detections = total_detections
        database.commit()
        logger.info(
            "Detection job %s completed: processed=%s failed=%s detections=%s device=%s",
            job.id, processed, failed, total_detections, job.processing_device,
        )
    except Exception as exc:
        logger.exception("Detection job %s failed", job_id)
        database.rollback()
        job = database.get(DetectionJob, job_id)
        if job:
            job.status = "failed"
            job.error_message = str(exc)
            job.completed_at = datetime.utcnow()
            database.commit()
    finally:
        database.close()
