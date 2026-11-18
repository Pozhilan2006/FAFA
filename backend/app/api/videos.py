"""Video ingestion, processing state, and storage-backed media endpoints."""
from pathlib import Path
from fastapi import APIRouter, BackgroundTasks, Depends, File, HTTPException, Query, UploadFile, status
from fastapi.responses import FileResponse
from sqlalchemy import func, select
from sqlalchemy.orm import Session
from ..core.config import settings
from ..database.connection import get_db
from ..database.models import ExtractedFrame, ProcessingJob, Video
from ..schemas.video import FramePage, FrameResponse, ProcessRequest, ProcessingStatusResponse, UploadResponse, VideoMetadataResponse
from ..services.metadata_extractor import extract_metadata
from ..services.video_validation import safe_upload_name, save_upload, validate_decodable_video
from ..workers.video_worker import process_video

router = APIRouter(prefix="/videos", tags=["videos"])

def video_response(video: Video) -> VideoMetadataResponse:
    return VideoMetadataResponse(video_id=video.id, original_filename=video.original_filename, file_size=video.file_size, format=video.format, duration_seconds=video.duration_seconds, width=video.width, height=video.height, resolution=f"{video.width}x{video.height}" if video.width and video.height else None, fps=video.original_fps, total_frames=video.total_frames, aspect_ratio=video.aspect_ratio, codec=video.codec, status=video.upload_status, created_at=video.created_at)

def get_video_or_404(video_id: str, database: Session) -> Video:
    video = database.get(Video, video_id)
    if not video: raise HTTPException(status_code=404, detail="Video was not found.")
    return video

def job_response(job: ProcessingJob) -> ProcessingStatusResponse:
    attempted = job.frames_processed + job.frames_failed
    if job.status == "completed":
        progress = 100.0
    elif job.frames_expected and job.frames_expected > 0:
        progress = round(min(100, max(0, (attempted / job.frames_expected) * 100)), 2)
    else:
        progress = 0.0
    return ProcessingStatusResponse(job_id=job.id, video_id=job.video_id, status=job.status, sampling_fps=job.sampling_fps, frames_expected=job.frames_expected, frames_processed=job.frames_processed, frames_failed=job.frames_failed, progress_percentage=progress, error_message=job.error_message, started_at=job.started_at, completed_at=job.completed_at)

@router.post("/upload", response_model=UploadResponse, status_code=status.HTTP_201_CREATED)
async def upload_video(file: UploadFile = File(...), database: Session = Depends(get_db)) -> UploadResponse:
    original_name, stored_name = safe_upload_name(file.filename)
    target = settings.storage_path / "uploads" / stored_name
    size = await save_upload(file, target, settings.max_upload_size_mb * 1024 * 1024)
    try:
        validate_decodable_video(target); metadata = extract_metadata(target)
    except ValueError as exc:
        target.unlink(missing_ok=True); raise HTTPException(status_code=422, detail=str(exc)) from exc
    video = Video(original_filename=original_name, stored_filename=stored_name, file_path=str(target), file_size=size, **metadata)
    database.add(video); database.commit(); database.refresh(video)
    return UploadResponse(video_id=video.id, filename=video.original_filename, status="uploaded", message="Video uploaded and validated successfully.")

@router.get("", response_model=list[VideoMetadataResponse])
def list_videos(database: Session = Depends(get_db)) -> list[VideoMetadataResponse]:
    return [video_response(video) for video in database.scalars(select(Video).order_by(Video.created_at.desc())).all()]

@router.get("/{video_id}", response_model=VideoMetadataResponse)
def get_video(video_id: str, database: Session = Depends(get_db)) -> VideoMetadataResponse:
    return video_response(get_video_or_404(video_id, database))

@router.post("/{video_id}/process", response_model=ProcessingStatusResponse, status_code=status.HTTP_202_ACCEPTED)
def start_processing(video_id: str, payload: ProcessRequest, background_tasks: BackgroundTasks, database: Session = Depends(get_db)) -> ProcessingStatusResponse:
    video = get_video_or_404(video_id, database)
    active = database.scalar(select(ProcessingJob).where(ProcessingJob.video_id == video.id, ProcessingJob.status.in_(["queued", "processing"])))
    if active and not payload.force: return job_response(active)
    job = ProcessingJob(video_id=video.id, sampling_fps=payload.sampling_fps)
    database.add(job); database.commit(); database.refresh(job)
    background_tasks.add_task(process_video, job.id)
    return job_response(job)

@router.get("/{video_id}/status", response_model=ProcessingStatusResponse)
def processing_status(video_id: str, database: Session = Depends(get_db)) -> ProcessingStatusResponse:
    get_video_or_404(video_id, database)
    job = database.scalar(select(ProcessingJob).where(ProcessingJob.video_id == video_id).order_by(ProcessingJob.started_at.desc(), ProcessingJob.id.desc()))
    if not job: raise HTTPException(status_code=404, detail="No processing job exists for this video.")
    return job_response(job)

@router.get("/{video_id}/frames", response_model=FramePage)
def list_frames(video_id: str, offset: int = Query(0, ge=0), limit: int = Query(24, ge=1, le=100), database: Session = Depends(get_db)) -> FramePage:
    get_video_or_404(video_id, database)
    total = database.scalar(select(func.count()).select_from(ExtractedFrame).where(ExtractedFrame.video_id == video_id)) or 0
    frames = database.scalars(select(ExtractedFrame).where(ExtractedFrame.video_id == video_id).order_by(ExtractedFrame.frame_number).offset(offset).limit(limit)).all()
    return FramePage(items=[FrameResponse(frame_id=f.id, video_id=f.video_id, frame_number=f.frame_number, timestamp_seconds=f.timestamp_seconds, original_width=f.original_width, original_height=f.original_height, processed_width=f.processed_width, processed_height=f.processed_height, image_url=f"/api/videos/{f.video_id}/frames/{f.id}") for f in frames], offset=offset, limit=limit, total=total)

@router.get("/{video_id}/preview")
def preview_video(video_id: str, database: Session = Depends(get_db)) -> FileResponse:
    video = get_video_or_404(video_id, database); path = Path(video.file_path)
    if not path.is_file(): raise HTTPException(status_code=410, detail="The video file is no longer available.")
    return FileResponse(path, media_type={"mp4": "video/mp4", "mov": "video/quicktime", "avi": "video/x-msvideo"}.get(video.format, "application/octet-stream"), filename=video.original_filename)

@router.get("/{video_id}/frames/{frame_id}")
def get_frame(video_id: str, frame_id: str, database: Session = Depends(get_db)) -> FileResponse:
    frame = database.scalar(select(ExtractedFrame).where(ExtractedFrame.id == frame_id, ExtractedFrame.video_id == video_id))
    if not frame: raise HTTPException(status_code=404, detail="Frame was not found.")
    path = Path(frame.processed_frame_path or frame.original_frame_path)
    if not path.is_file(): raise HTTPException(status_code=410, detail="Frame file is no longer available.")
    return FileResponse(path, media_type="image/jpeg")
