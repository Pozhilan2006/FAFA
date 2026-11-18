"""Detection result filtering and coordinate normalization."""
from __future__ import annotations

from typing import Any

TARGET_CLASS_NAMES = {"person", "sports ball"}


def clamp(value: float, low: float, high: float) -> float:
    return max(low, min(high, value))


def to_original_coords(
    box: tuple[float, float, float, float],
    inference_width: int,
    inference_height: int,
    original_width: int,
    original_height: int,
) -> tuple[float, float, float, float]:
    sx = (original_width / inference_width) if inference_width else 1.0
    sy = (original_height / inference_height) if inference_height else 1.0
    x1, y1, x2, y2 = box
    ox1 = clamp(x1 * sx, 0.0, float(original_width))
    oy1 = clamp(y1 * sy, 0.0, float(original_height))
    ox2 = clamp(x2 * sx, 0.0, float(original_width))
    oy2 = clamp(y2 * sy, 0.0, float(original_height))
    if ox2 < ox1:
        ox1, ox2 = ox2, ox1
    if oy2 < oy1:
        oy1, oy2 = oy2, oy1
    return ox1, oy1, ox2, oy2


def normalized_bbox(x1: float, y1: float, x2: float, y2: float, width: int, height: int) -> dict[str, float]:
    if width <= 0 or height <= 0:
        return {"x_center": 0.0, "y_center": 0.0, "width": 0.0, "height": 0.0}
    bw = max(0.0, x2 - x1)
    bh = max(0.0, y2 - y1)
    cx = x1 + bw / 2.0
    cy = y1 + bh / 2.0
    return {
        "x_center": cx / width,
        "y_center": cy / height,
        "width": bw / width,
        "height": bh / height,
    }


def parse_yolo_result(
    result: Any,
    frame_number: int,
    timestamp_seconds: float,
    original_width: int,
    original_height: int,
    confidence_threshold: float,
    allowed_names: set[str] | None = None,
) -> list[dict[str, Any]]:
    allowed = allowed_names or TARGET_CLASS_NAMES
    names = getattr(result, "names", None) or {}
    if isinstance(names, list):
        names = {i: str(n) for i, n in enumerate(names)}
    boxes = getattr(result, "boxes", None)
    if boxes is None:
        return []
    orig_shape = getattr(result, "orig_shape", None) or (original_height, original_width)
    inf_h, inf_w = int(orig_shape[0]), int(orig_shape[1])
    detections: list[dict[str, Any]] = []
    xyxy = boxes.xyxy
    confs = boxes.conf
    clss = boxes.cls
    if xyxy is None or confs is None or clss is None:
        return []
    try:
        xyxy_list = xyxy.detach().cpu().tolist()
        conf_list = confs.detach().cpu().tolist()
        cls_list = clss.detach().cpu().tolist()
    except Exception:
        xyxy_list = xyxy.tolist()
        conf_list = confs.tolist()
        cls_list = clss.tolist()
    for coords, conf, cls_id in zip(xyxy_list, conf_list, cls_list):
        class_id = int(cls_id)
        class_name = str(names.get(class_id, class_id))
        confidence = float(conf)
        if class_name not in allowed or confidence < confidence_threshold:
            continue
        x1, y1, x2, y2 = (float(coords[0]), float(coords[1]), float(coords[2]), float(coords[3]))
        ox1, oy1, ox2, oy2 = to_original_coords((x1, y1, x2, y2), inf_w, inf_h, original_width, original_height)
        detections.append(
            {
                "frame_number": frame_number,
                "timestamp_seconds": timestamp_seconds,
                "class_id": class_id,
                "class_name": class_name,
                "confidence": confidence,
                "x_min": ox1,
                "y_min": oy1,
                "x_max": ox2,
                "y_max": oy2,
                "image_width": original_width,
                "image_height": original_height,
                "normalized_bbox": normalized_bbox(ox1, oy1, ox2, oy2, original_width, original_height),
            }
        )
    return detections
