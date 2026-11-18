from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace

import pytest

from tests.detection.conftest import upload_and_process, make_test_image


class FakeBoxes:
    def __init__(self, xyxy, conf, cls):
        import numpy as np
        self._xyxy = np.array(xyxy, dtype=float); self._conf = np.array(conf, dtype=float); self._cls = np.array(cls, dtype=float)
    class A:
        def __init__(self,a): self.a=a
        def detach(self): return self
        def cpu(self): return self
        def tolist(self): return self.a.tolist()
    @property
    def xyxy(self): return self.A(self._xyxy)
    @property
    def conf(self): return self.A(self._conf)
    @property
    def cls(self): return self.A(self._cls)

class FakeResult:
    def __init__(self, h, w):
        self.boxes = FakeBoxes([[5,5,20,30],[10,10,15,15]], [0.91,0.77], [0,32])
        self.names = {0:"person", 32:"sports ball"}
        self.orig_shape = (h,w)

class FakeModel:
    names = {0:"person", 32:"sports ball"}
    device = "cpu"
    def predict(self, images, **kwargs):
        out = []
        for img in images:
            h,w = img.shape[:2]
            out.append(FakeResult(h,w))
        return out


def _patch_model(monkeypatch):
    from backend.app.services import detection as det_pkg
    from backend.app.services.detection import model_loader
    fake = FakeModel()
    monkeypatch.setattr(model_loader, "load_model", lambda force_reload=False: (fake, model_loader.ModelInfo("fake-yolo.pt", None, "cpu", {0:"person",32:"sports ball"}, ["person","sports ball"])) )
    monkeypatch.setattr(model_loader, "describe_model", lambda: {"model_name":"fake-yolo.pt","model_path":None,"device":"cpu","loaded":True,"class_names":{0:"person",32:"sports ball"},"supported_target_classes":["person","sports ball"]})


def test_detection_model_info_endpoint(app_client):
    r = app_client.get("/api/detection/model-info")
    assert r.status_code == 200
    body = r.json()
    assert "model_name" in body and "supported_target_classes" in body


def test_start_detection_requires_extracted_frames(app_client, tmp_path):
    # upload but do not process
    from tests.detection.conftest import make_test_video
    video_path = tmp_path / "v.avi"; make_test_video(video_path)
    up = app_client.post("/api/videos/upload", files={"file": ("v.avi", video_path.read_bytes(), "video/x-msvideo")})
    vid = up.json()["video_id"]
    r = app_client.post(f"/api/detection/{vid}/start", json={"confidence_threshold":0.35,"batch_size":2,"max_frames":10,"process_all_frames":False})
    assert r.status_code == 409


def test_detection_job_flow_results_and_annotated_frame(app_client, tmp_path, monkeypatch):
    _patch_model(monkeypatch)
    video_id, _ = upload_and_process(app_client, tmp_path, sampling_fps=10.0)
    start = app_client.post(f"/api/detection/{video_id}/start", json={"confidence_threshold":0.35,"batch_size":2,"max_frames":5,"process_all_frames":False})
    assert start.status_code == 202, start.text
    job = start.json()
    assert job["status"] in {"queued","completed"}
    status = app_client.get(f"/api/detection/{video_id}/status")
    assert status.status_code == 200
    sj = status.json()
    assert sj["status"] == "completed"
    assert sj["processed_frames"] > 0
    assert sj["total_detections"] >= sj["processed_frames"]

    summary = app_client.get(f"/api/detection/{video_id}/summary")
    assert summary.status_code == 200
    sm = summary.json()
    assert sm["total_person_detections"] > 0
    assert sm["total_sports_ball_detections"] > 0
    assert sm["frames_processed"] == sj["processed_frames"]
    assert sm["frames_with_detections"] <= sm["frames_processed"]

    results = app_client.get(f"/api/detection/{video_id}/results?offset=0&limit=10")
    assert results.status_code == 200
    page = results.json()
    assert page["total"] == sj["processed_frames"]
    assert len(page["items"]) > 0
    item = page["items"][0]
    assert item["frame_number"] >= 0
    assert "timestamp_seconds" in item
    assert item["annotated_image_url"]
    assert item["detection_count"] == len(item["detections"])
    det = item["detections"][0]
    assert {"detection_id","video_id","frame_id","frame_number","timestamp_seconds","class_id","class_name","confidence","bbox","image_width","image_height"}.issubset(det.keys())
    assert det["video_id"] == video_id
    assert det["frame_id"] == item["frame_id"]

    frame_res = app_client.get(f"/api/detection/{video_id}/frames/{item['frame_id']}")
    assert frame_res.status_code == 200
    assert frame_res.json()["frame_number"] == item["frame_number"]

    ann = app_client.get(item["annotated_image_url"].replace("http://testserver",""))
    assert ann.status_code == 200
    assert ann.headers["content-type"].startswith("image/")


def test_missing_video_and_duplicate_job_handling(app_client, tmp_path, monkeypatch):
    _patch_model(monkeypatch)
    r = app_client.post("/api/detection/missing/start", json={"confidence_threshold":0.35,"batch_size":2,"max_frames":5,"process_all_frames":False})
    assert r.status_code == 404
    video_id, _ = upload_and_process(app_client, tmp_path, sampling_fps=10.0)
    # simulate active job
    from backend.app.database.connection import SessionLocal
    from backend.app.database.models import DetectionJob
    db = SessionLocal()
    try:
        db.add(DetectionJob(video_id=video_id, model_name="m", confidence_threshold=0.35, batch_size=2, status="processing", total_frames=1))
        db.commit()
    finally:
        db.close()
    dup = app_client.post(f"/api/detection/{video_id}/start", json={"confidence_threshold":0.35,"batch_size":2,"max_frames":5,"process_all_frames":False})
    assert dup.status_code == 409


def test_failed_frame_handling_in_worker(tmp_path, monkeypatch):
    # unit-level worker behavior with a missing image path should mark failed frame, not crash job
    from backend.app.core import config
    from backend.app.database import connection
    from backend.app.database.base import Base
    from backend.app.database.models import DetectionJob, ExtractedFrame, Video
    import sqlalchemy
    db_path = tmp_path / "w.db"
    config.settings.database_url = f"sqlite:///{db_path}"
    config.settings.storage_path = tmp_path / "storage"
    connection.engine = sqlalchemy.create_engine(config.settings.database_url, connect_args={"check_same_thread": False})
    connection.SessionLocal.configure(bind=connection.engine)
    Base.metadata.create_all(connection.engine)
    db = connection.SessionLocal()
    try:
        video = Video(original_filename="v.avi", stored_filename="v.avi", file_path=str(tmp_path/"v.avi"), file_size=1, format="avi")
        db.add(video); db.commit(); db.refresh(video)
        db.add(ExtractedFrame(video_id=video.id, frame_number=1, timestamp_seconds=0.1, original_frame_path=str(tmp_path/"missing.jpg"), processed_frame_path=None, original_width=64, original_height=48, processed_width=64, processed_height=48))
        job = DetectionJob(video_id=video.id, model_name="fake", confidence_threshold=0.35, batch_size=2, status="queued", total_frames=1)
        db.add(job); db.commit(); db.refresh(job)
        job_id = job.id
    finally:
        db.close()
    # patch model loader used by worker
    from backend.app.services.detection import model_loader
    fake = FakeModel()
    monkeypatch.setattr(model_loader, "load_model", lambda force_reload=False: (fake, model_loader.ModelInfo("fake-yolo.pt", None, "cpu", {0:"person",32:"sports ball"}, ["person","sports ball"])) )
    from backend.app.workers.detection_worker import process_detection
    process_detection(job_id, max_frames=1)
    db = connection.SessionLocal()
    try:
        job = db.get(DetectionJob, job_id)
        assert job.status == "completed"
        assert job.failed_frames == 1
        assert job.processed_frames == 0
    finally:
        db.close()
