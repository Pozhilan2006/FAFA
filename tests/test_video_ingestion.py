from pathlib import Path
from types import SimpleNamespace
import cv2
import numpy as np
import pytest
from fastapi.testclient import TestClient


@pytest.fixture()
def client(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> TestClient:
    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{tmp_path / 'test.db'}")
    monkeypatch.setenv("STORAGE_PATH", str(tmp_path / "storage"))
    from backend.app.core import config
    config.settings.database_url = f"sqlite:///{tmp_path / 'test.db'}"
    config.settings.storage_path = tmp_path / "storage"
    from backend.app.database import connection
    from backend.app.database.base import Base
    connection.engine = __import__("sqlalchemy").create_engine(config.settings.database_url, connect_args={"check_same_thread": False})
    connection.SessionLocal.configure(bind=connection.engine)
    Base.metadata.create_all(connection.engine)
    from backend.app.main import app
    with TestClient(app) as test_client:
        yield test_client


def make_video(path: Path) -> None:
    codec = "MJPG" if path.suffix == ".avi" else "mp4v"
    writer = cv2.VideoWriter(str(path), cv2.VideoWriter_fourcc(*codec), 10, (64, 32))
    assert writer.isOpened()
    for value in range(10): writer.write(np.full((32, 64, 3), value * 20, dtype=np.uint8))
    writer.release()


def test_upload_process_and_list_frames(client: TestClient, tmp_path: Path) -> None:
    video_path = tmp_path / "match.avi"; make_video(video_path)
    response = client.post("/api/videos/upload", files={"file": ("match.avi", video_path.read_bytes(), "video/x-msvideo")})
    assert response.status_code == 201
    video_id = response.json()["video_id"]
    assert client.get(f"/api/videos/{video_id}").json()["total_frames"] == 10
    job = client.post(f"/api/videos/{video_id}/process", json={"sampling_fps": 2}).json()
    assert job["status"] in {"queued", "completed"}
    status = client.get(f"/api/videos/{video_id}/status").json()
    assert status["status"] == "completed"
    assert status["progress_percentage"] == 100
    frames = client.get(f"/api/videos/{video_id}/frames").json()
    assert frames["total"] == 2
    assert frames["items"][1]["frame_number"] == 5
    assert frames["items"][0]["image_url"].startswith(f"/api/videos/{video_id}/frames/")
    image = client.get(frames["items"][0]["image_url"])
    assert image.status_code == 200
    assert image.headers["content-type"] == "image/jpeg"


def test_rejects_non_video(client: TestClient) -> None:
    response = client.post("/api/videos/upload", files={"file": ("bad.mp4", b"not a video", "video/mp4")})
    assert response.status_code == 422


@pytest.mark.parametrize(("job_status", "expected_frames", "processed", "failed", "expected_progress"), [
    ("queued", None, 0, 0, 0),
    ("processing", 100, 45, 0, 45),
    ("completed", None, 0, 0, 100),
    ("failed", None, 0, 0, 0),
    ("processing", 10, 20, 0, 100),
    ("processing", 10, -5, 0, 0),
])
def test_processing_progress_is_always_clamped_number(job_status: str, expected_frames: int | None, processed: int, failed: int, expected_progress: float) -> None:
    from backend.app.api.videos import job_response
    response = job_response(SimpleNamespace(id="job", video_id="video", status=job_status, sampling_fps=2, frames_expected=expected_frames, frames_processed=processed, frames_failed=failed, error_message="failed" if job_status == "failed" else None, started_at=None, completed_at=None))
    assert response.progress_percentage == expected_progress
    if job_status == "failed":
        assert response.error_message == "failed"


@pytest.mark.parametrize("suffix,mime", [(".mp4", "video/mp4"), (".mov", "video/quicktime"), (".avi", "video/x-msvideo")])
def test_accepts_supported_decodable_formats(client: TestClient, tmp_path: Path, suffix: str, mime: str) -> None:
    video_path = tmp_path / f"match{suffix}"
    make_video(video_path)
    response = client.post("/api/videos/upload", files={"file": (video_path.name, video_path.read_bytes(), mime)})
    assert response.status_code == 201
