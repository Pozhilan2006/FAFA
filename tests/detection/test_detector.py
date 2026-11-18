from __future__ import annotations

from types import SimpleNamespace

import numpy as np

from backend.app.services.detection.postprocessing import (
    TARGET_CLASS_NAMES,
    clamp,
    normalized_bbox,
    parse_yolo_result,
    to_original_coords,
)
from backend.app.services.detection.model_loader import get_model_info


class FakeBoxes:
    def __init__(self, xyxy, conf, cls):
        self.xyxy = np.array(xyxy, dtype=float)
        self.conf = np.array(conf, dtype=float)
        self.cls = np.array(cls, dtype=float)

    class _Arr:
        def __init__(self, arr): self.arr = arr
        def detach(self): return self
        def cpu(self): return self
        def tolist(self): return self.arr.tolist()

    @property
    def xyxy(self):
        return self._Arr(self._xyxy)
    @xyxy.setter
    def xyxy(self, v): self._xyxy = v
    @property
    def conf(self):
        return self._Arr(self._conf)
    @conf.setter
    def conf(self, v): self._conf = v
    @property
    def cls(self):
        return self._Arr(self._cls)
    @cls.setter
    def cls(self, v): self._cls = v


class FakeResult:
    def __init__(self, boxes, names, orig_shape=(48, 64)):
        self.boxes = boxes
        self.names = names
        self.orig_shape = orig_shape


def test_target_classes():
    assert "person" in TARGET_CLASS_NAMES and "sports ball" in TARGET_CLASS_NAMES


def test_clamp_and_coordinates_validation():
    assert clamp(-5, 0, 10) == 0
    assert clamp(15, 0, 10) == 10
    x1, y1, x2, y2 = to_original_coords((10, 10, 30, 30), 64, 48, 128, 96)
    assert (x1, y1, x2, y2) == (20.0, 20.0, 60.0, 60.0)
    # clamp within bounds and order
    x1, y1, x2, y2 = to_original_coords((-10, 50, 200, -5), 64, 48, 64, 48)
    assert 0 <= x1 <= 64 and 0 <= x2 <= 64 and 0 <= y1 <= 48 and 0 <= y2 <= 48
    assert x2 >= x1 and y2 >= y1


def test_normalized_bbox():
    nb = normalized_bbox(10, 20, 30, 60, 100, 200)
    assert nb["width"] == 0.2 and nb["height"] == 0.2
    assert abs(nb["x_center"] - 0.2) < 1e-9
    assert abs(nb["y_center"] - 0.2) < 1e-9


def test_parse_person_and_sports_ball_and_confidence_filtering():
    names = {0: "person", 32: "sports ball", 2: "car"}
    boxes = FakeBoxes([[1, 2, 10, 20], [5, 5, 9, 9], [3, 3, 8, 8]], [0.9, 0.2, 0.8], [0, 32, 2])
    res = FakeResult(boxes, names, orig_shape=(48, 64))
    detections = parse_yolo_result(res, frame_number=12, timestamp_seconds=1.25, original_width=64, original_height=48, confidence_threshold=0.35)
    assert len(detections) == 1
    d = detections[0]
    assert d["class_name"] == "person" and d["class_id"] == 0
    assert d["frame_number"] == 12 and d["timestamp_seconds"] == 1.25
    assert d["confidence"] == 0.9
    assert d["image_width"] == 64 and d["image_height"] == 48

    detections_ball = parse_yolo_result(res, frame_number=13, timestamp_seconds=1.3, original_width=64, original_height=48, confidence_threshold=0.1)
    assert {d["class_name"] for d in detections_ball} == {"person", "sports ball"}


def test_get_model_info_extracts_names():
    model = SimpleNamespace(names={0: "person", 32: "sports ball"})
    info = get_model_info(model, "yolov8n.pt", None, "cpu")
    assert info.class_names[0] == "person"
    assert "sports ball" in info.supported_target_classes
