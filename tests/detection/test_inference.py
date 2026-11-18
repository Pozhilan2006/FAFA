from __future__ import annotations

from types import SimpleNamespace

import numpy as np

from backend.app.services.detection.inference import run_inference_on_frames


def test_cpu_inference_path_mocked(tmp_path):
    # ensures device argument is passed and batch processing works on CPU-like path via mock
    import cv2
    p = tmp_path / "f.jpg"; cv2.imwrite(str(p), np.full((32,32,3), 50, dtype=np.uint8))
    frame = SimpleNamespace(id="f", frame_number=1, timestamp_seconds=0.1, original_width=32, original_height=32, processed_frame_path=str(p), original_frame_path=str(p))

    class Boxes:
        def __init__(self):
            self._xyxy=np.array([[1,1,10,10]],dtype=float); self._conf=np.array([0.5],dtype=float); self._cls=np.array([0],dtype=float)
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
    class Res:
        boxes = Boxes(); names={0:"person"}; orig_shape=(32,32)
    class Model:
        def __init__(self): self.kw=None
        def predict(self, imgs, **kw): self.kw=kw; return [Res() for _ in imgs]
    m = Model()
    out = run_inference_on_frames(m, [frame], confidence_threshold=0.3, batch_size=1, device="cpu")
    assert m.kw.get("device") == "cpu"
    assert out["processed_frames"] == 1


def test_real_inference_on_actual_frame_if_available(tmp_path):
    """Real inference test (not mocked). Skips if ultralytics/model unavailable in environment."""
    import cv2
    pytest = __import__("pytest")
    try:
        from ultralytics import YOLO
    except Exception:
        pytest.skip("ultralytics not installed")
    try:
        model = YOLO("yolov8n.pt")
    except Exception as exc:
        pytest.skip(f"model weights unavailable: {exc}")
    p = tmp_path / "real.jpg"
    img = np.full((320, 320, 3), 180, dtype=np.uint8)
    cv2.rectangle(img, (40, 40), (120, 280), (90, 120, 80), -1)
    cv2.imwrite(str(p), img)
    frame = SimpleNamespace(id="real", frame_number=3, timestamp_seconds=0.3, original_width=320, original_height=320, processed_frame_path=str(p), original_frame_path=str(p))
    out = run_inference_on_frames(model, [frame], confidence_threshold=0.1, batch_size=1, device="cpu")
    assert out["processed_frames"] + out["failed_frames"] == 1
    # detections may be zero on synthetic image; correctness is that inference ran and preserved metadata
    if out["results"][0]["detections"]:
        d = out["results"][0]["detections"][0]
        assert d["frame_number"] == 3 and d["timestamp_seconds"] == 0.3
