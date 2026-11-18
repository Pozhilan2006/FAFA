from __future__ import annotations

from pathlib import Path
import cv2
import numpy as np
import pytest
from fastapi.testclient import TestClient


def make_test_video(path: Path, frames: int = 12, fps: int = 10, size=(64, 48)) -> None:
    codec = "MJPG" if path.suffix.lower() == ".avi" else "mp4v"
    writer = cv2.VideoWriter(str(path), cv2.VideoWriter_fourcc(*codec), fps, size)
    assert writer.isOpened(), "Failed to open VideoWriter for test video"
    for i in range(frames):
        img = np.full((size[1], size[0], 3), (i * 10) % 255, dtype=np.uint8)
        cv2.circle(img, (10 + i % 20, 10 + (i * 2) % 20), 6, (255, 255, 255), -1)
        writer.write(img)
    writer.release()


def make_test_image(path: Path, size=(64, 48)) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    img = np.full((size[1], size[0], 3), 120, dtype=np.uint8)
    cv2.rectangle(img, (5, 5), (20, 30), (0, 255, 0), -1)
    assert cv2.imwrite(str(path), img)
    return path


@pytest.fixture()
def app_client(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> TestClient:
    db_path = tmp_path / "test.db"
    storage_path = tmp_path / "storage"
    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{db_path}")
    monkeypatch.setenv("STORAGE_PATH", str(storage_path))

    # reset settings
    from backend.app.core import config
    config.settings.database_url = f"sqlite:///{db_path}"
    config.settings.storage_path = storage_path
    config.settings.detection_model_name = "yolov8n.pt"
    config.settings.detection_model_path = None

    # reset DB engine/session
    import sqlalchemy
    from backend.app.database import connection
    from backend.app.database.base import Base
    from backend.app.database import models  # noqa: F401
    connection.engine = sqlalchemy.create_engine(config.settings.database_url, connect_args={"check_same_thread": False})
    connection.SessionLocal.configure(bind=connection.engine)
    Base.metadata.drop_all(connection.engine)
    Base.metadata.create_all(connection.engine)

    from backend.app.main import app
    with TestClient(app) as client:
        yield client


def upload_and_process(client: TestClient, tmp_path: Path, sampling_fps: float = 5.0) -> tuple[str, str]:
    video_path = tmp_path / "match.avi"
    make_test_video(video_path, frames=20, fps=10)
    resp = client.post("/api/videos/upload", files={"file": ("match.avi", video_path.read_bytes(), "video/x-msvideo")})
    assert resp.status_code == 201, resp.text
    video_id = resp.json()["video_id"]
    job = client.post(f"/api/videos/{video_id}/process", json={"sampling_fps": sampling_fps})
    assert job.status_code in (200, 202), job.text
    status = client.get(f"/api/videos/{video_id}/status")
    assert status.status_code == 200
    assert status.json()["status"] == "completed"
    return video_id, status.json()["job_id"]
