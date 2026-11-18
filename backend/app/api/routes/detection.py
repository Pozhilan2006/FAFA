"""Object detection endpoints: model info, jobs, results, and annotated frames."""
from __future__ import annotations

from pathlib import Path

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query
from fastapi.responses import FileResponse
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from ...core.config import settings
from ...database.connection import get_db
from ...database.models import AnnotatedFrame, DetectionJob, ExtractedFrame, ObjectDetection, Video
from ...schemas.detection import (
    BBox,
    DetectionFrameResult,
    DetectionJobResponse,
    DetectionRecord,
    DetectionResultsPage,
    DetectionStartRequest,
    DetectionSummaryResponse,
    ModelInfoResponse,
    NormalizedBBox,
)
from ...services.detection.model_loader import describe_model
from ...workers.detection_worker import process_detection

router = APIRouter(prefix="/detection", tags=["detection"])


def _get_video(video_id: str, db: Session) -> Video:
    video = db.get(Video, video_id)
    if not video:
        raise HTTPException(status_code=404, detail="Video was not found.")
    return video


def _latest_job(video_id: str, db: Session) -> DetectionJob | None:
    return db.scalar(
        select(DetectionJob).where(DetectionJob.video_id == video_id).order_by(DetectionJob.started_at.desc().nullslast(), DetectionJob.id.desc())
    )


def _job_response(job: DetectionJob) -> DetectionJobResponse:
    attempted = job.processed_frames + job.failed_frames
    if job.status == "completed":
        progress = 100.0
    elif job.total_frames and job.total_frames > 0:
        progress = round(min(100.0, max(0.0, (attempted / job.total_frames) * 100.0)), 2)
    else:
        progress = 0.0
    duration = None
    if job.started_at:
        end = job.completed_at or __import__("datetime").datetime.utcnow()
        duration = max(0.0, (end - job.started_at).total_seconds())
    return DetectionJobResponse(
        job_id=job.id,
        video_id=job.video_id,
        status=job.status,
        model_name=job.model_name,
        confidence_threshold=job.confidence_threshold,
        batch_size=job.batch_size,
        total_frames=job.total_frames,
        processed_frames=job.processed_frames,
        failed_frames=job.failed_frames,
        total_detections=job.total_detections,
        processing_device=job.processing_device,
        progress_percentage=progress,
        processing_duration_seconds=round(duration, 3) if duration is not None else None,
        error_message=job.error_message,
        started_at=job.started_at,
        completed_at=job.completed_at,
    )


@router.get("/model-info", response_model=ModelInfoResponse)
def model_info() -> ModelInfoResponse:
    try:
        info = describe_model()
        return ModelInfoResponse(
            model_name=info["model_name"],
            model_path=info.get("model_path"),
            device=info["device"],
            loaded=bool(info.get("loaded")),
            class_names=info.get("class_names"),
            supported_target_classes=info.get("supported_target_classes") or ["person", "sports ball"],
            confidence_default=settings.detection_default_confidence,
            batch_size_default=settings.detection_default_batch_size,
        )
    except Exception as exc:
        return ModelInfoResponse(
            model_name=settings.detection_model_name,
            model_path=settings.detection_model_path,
            device=settings.detection_device or "cpu",
            loaded=False,
            class_names=None,
            supported_target_classes=["person", "sports ball"],
            confidence_default=settings.detection_default_confidence,
            batch_size_default=settings.detection_default_batch_size,
            detail=str(exc),
        )


@router.post("/{video_id}/start", response_model=DetectionJobResponse, status_code=202)
def start_detection(video_id: str, payload: DetectionStartRequest, background_tasks: BackgroundTasks, db: Session = Depends(get_db)) -> DetectionJobResponse:
    _get_video(video_id, db)
    active = db.scalar(select(DetectionJob).where(DetectionJob.video_id == video_id, DetectionJob.status.in_(["queued", "processing"])))
    if active:
        raise HTTPException(status_code=409, detail=f"Detection job {active.id} is already {active.status} for this video.")
    frame_count = db.scalar(select(func.count()).select_from(ExtractedFrame).where(ExtractedFrame.video_id == video_id)) or 0
    if frame_count == 0:
        raise HTTPException(status_code=409, detail="No extracted frames available. Run frame extraction before detection.")
    effective_total = frame_count if payload.process_all_frames else min(frame_count, payload.max_frames or frame_count)
    model = describe_model()
    job = DetectionJob(
        video_id=video_id,
        model_name=str(model.get("model_name") or settings.detection_model_name),
        confidence_threshold=payload.confidence_threshold,
        batch_size=payload.batch_size,
        status="queued",
        total_frames=effective_total,
        processing_device=str(model.get("device") or settings.detection_device or "cpu"),
    )
    db.add(job)
    db.commit()
    db.refresh(job)
    max_frames = None if payload.process_all_frames else payload.max_frames
    background_tasks.add_task(process_detection, job.id, max_frames)
    return _job_response(job)


@router.get("/{video_id}/status", response_model=DetectionJobResponse)
def detection_status(video_id: str, job_id: str | None = Query(None), db: Session = Depends(get_db)) -> DetectionJobResponse:
    _get_video(video_id, db)
    job = db.get(DetectionJob, job_id) if job_id else _latest_job(video_id, db)
    if not job or job.video_id != video_id:
        raise HTTPException(status_code=404, detail="No detection job exists for this video.")
    return _job_response(job)


@router.get("/{video_id}/summary", response_model=DetectionSummaryResponse)
def detection_summary(video_id: str, job_id: str | None = Query(None), db: Session = Depends(get_db)) -> DetectionSummaryResponse:
    _get_video(video_id, db)
    job = db.get(DetectionJob, job_id) if job_id else _latest_job(video_id, db)
    if not job or job.video_id != video_id:
        raise HTTPException(status_code=404, detail="No detection job exists for this video.")
    person = db.scalar(select(func.count()).select_from(ObjectDetection).where(ObjectDetection.detection_job_id == job.id, ObjectDetection.class_name == "person")) or 0
    ball = db.scalar(select(func.count()).select_from(ObjectDetection).where(ObjectDetection.detection_job_id == job.id, ObjectDetection.class_name == "sports ball")) or 0
    frames_with = db.scalar(select(func.count(func.distinct(ObjectDetection.frame_id))).where(ObjectDetection.detection_job_id == job.id)) or 0
    avg_conf = db.scalar(select(func.avg(ObjectDetection.confidence)).where(ObjectDetection.detection_job_id == job.id))
    frames_without = max(0, int(job.processed_frames) - int(frames_with))
    duration = None
    if job.started_at:
        end = job.completed_at or __import__("datetime").datetime.utcnow()
        duration = max(0.0, (end - job.started_at).total_seconds())
    avg_per_frame = (duration / job.processed_frames) if duration and job.processed_frames else None
    fps = (job.processed_frames / duration) if duration and duration > 0 and job.processed_frames else None
    return DetectionSummaryResponse(
        job_id=job.id,
        video_id=job.video_id,
        total_person_detections=int(person),
        total_sports_ball_detections=int(ball),
        total_detections=int(job.total_detections),
        frames_processed=int(job.processed_frames),
        frames_with_detections=int(frames_with),
        frames_without_detections=int(frames_without),
        failed_frames=int(job.failed_frames),
        average_confidence=float(avg_conf) if avg_conf is not None else None,
        inference_seconds=round(duration, 3) if duration is not None else None,
        average_inference_seconds_per_frame=round(avg_per_frame, 6) if avg_per_frame is not None else None,
        frames_per_second=round(fps, 4) if fps is not None else None,
    )


def _record(det: ObjectDetection) -> DetectionRecord:
    nb = det.normalized_bbox or {}
    return DetectionRecord(
        detection_id=det.id,
        video_id=det.video_id,
        frame_id=det.frame_id,
        frame_number=det.frame_number,
        timestamp_seconds=det.timestamp_seconds,
        class_id=det.class_id,
        class_name=det.class_name,
        confidence=det.confidence,
        bbox=BBox(x_min=det.x_min, y_min=det.y_min, x_max=det.x_max, y_max=det.y_max),
        image_width=det.image_width,
        image_height=det.image_height,
        normalized_bbox=NormalizedBBox(**nb) if {"x_center","y_center","width","height"}.issubset(nb.keys()) else None,
    )


@router.get("/{video_id}/results", response_model=DetectionResultsPage)
def detection_results(
    video_id: str,
    job_id: str | None = Query(None),
    offset: int = Query(0, ge=0),
    limit: int = Query(24, ge=1, le=100),
    db: Session = Depends(get_db),
) -> DetectionResultsPage:
    _get_video(video_id, db)
    job = db.get(DetectionJob, job_id) if job_id else _latest_job(video_id, db)
    if not job or job.video_id != video_id:
        raise HTTPException(status_code=404, detail="No detection job exists for this video.")
    total = db.scalar(select(func.count()).select_from(AnnotatedFrame).where(AnnotatedFrame.detection_job_id == job.id)) or 0
    ann_rows = db.execute(
        select(AnnotatedFrame, ExtractedFrame)
        .join(ExtractedFrame, ExtractedFrame.id == AnnotatedFrame.frame_id)
        .where(AnnotatedFrame.detection_job_id == job.id)
        .order_by(ExtractedFrame.frame_number)
        .offset(offset)
        .limit(limit)
    ).all()
    items: list[DetectionFrameResult] = []
    for ann, frame in ann_rows:
        dets = db.scalars(select(ObjectDetection).where(ObjectDetection.detection_job_id == job.id, ObjectDetection.frame_id == frame.id).order_by(ObjectDetection.confidence.desc())).all()
        recs = [_record(d) for d in dets]
        items.append(DetectionFrameResult(
            frame_id=frame.id,
            frame_number=frame.frame_number,
            timestamp_seconds=frame.timestamp_seconds,
            original_image_url=f"/api/videos/{video_id}/frames/{frame.id}",
            annotated_image_url=f"/api/detection/{video_id}/annotated/{frame.id}?job_id={job.id}",
            detection_count=len(recs),
            detected_class_names=sorted({r.class_name for r in recs}),
            detections=recs,
        ))
    return DetectionResultsPage(items=items, offset=offset, limit=limit, total=int(total))


@router.get("/{video_id}/frames/{frame_id}", response_model=DetectionFrameResult)
def detection_frame(video_id: str, frame_id: str, job_id: str | None = Query(None), db: Session = Depends(get_db)) -> DetectionFrameResult:
    _get_video(video_id, db)
    job = db.get(DetectionJob, job_id) if job_id else _latest_job(video_id, db)
    if not job or job.video_id != video_id:
        raise HTTPException(status_code=404, detail="No detection job exists for this video.")
    frame = db.get(ExtractedFrame, frame_id)
    if not frame or frame.video_id != video_id:
        raise HTTPException(status_code=404, detail="Frame was not found for this video.")
    ann = db.scalar(select(AnnotatedFrame).where(AnnotatedFrame.detection_job_id == job.id, AnnotatedFrame.frame_id == frame_id))
    dets = db.scalars(select(ObjectDetection).where(ObjectDetection.detection_job_id == job.id, ObjectDetection.frame_id == frame_id).order_by(ObjectDetection.confidence.desc())).all()
    recs = [_record(d) for d in dets]
    return DetectionFrameResult(
        frame_id=frame.id,
        frame_number=frame.frame_number,
        timestamp_seconds=frame.timestamp_seconds,
        original_image_url=f"/api/videos/{video_id}/frames/{frame.id}",
        annotated_image_url=f"/api/detection/{video_id}/annotated/{frame.id}?job_id={job.id}" if ann else None,
        detection_count=len(recs),
        detected_class_names=sorted({r.class_name for r in recs}),
        detections=recs,
    )


@router.get("/{video_id}/annotated/{frame_id}")
def annotated_frame(video_id: str, frame_id: str, job_id: str | None = Query(None), db: Session = Depends(get_db)) -> FileResponse:
    _get_video(video_id, db)
    job = db.get(DetectionJob, job_id) if job_id else _latest_job(video_id, db)
    if not job or job.video_id != video_id:
        raise HTTPException(status_code=404, detail="No detection job exists for this video.")
    ann = db.scalar(select(AnnotatedFrame).where(AnnotatedFrame.detection_job_id == job.id, AnnotatedFrame.frame_id == frame_id))
    if not ann:
        raise HTTPException(status_code=404, detail="Annotated frame was not found for this detection job.")
    path = Path(ann.annotated_frame_path)
    if not path.is_file():
        raise HTTPException(status_code=410, detail="Annotated frame file is no longer available.")
    return FileResponse(path, media_type="image/jpeg")
