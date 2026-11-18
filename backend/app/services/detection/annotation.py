"""Annotated frame rendering for detection results."""
from __future__ import annotations

from pathlib import Path
from typing import Iterable, Mapping

import cv2

COLORS = {
    "person": (56, 142, 60),       # green-ish BGR
    "sports ball": (0, 165, 255),  # orange BGR
}
DEFAULT_COLOR = (255, 200, 0)


def draw_detections(image, detections: Iterable[Mapping]):
    canvas = image.copy()
    for det in detections:
        name = str(det.get("class_name", "object"))
        conf = float(det.get("confidence", 0.0))
        x1, y1 = int(round(float(det["x_min"]))), int(round(float(det["y_min"])))
        x2, y2 = int(round(float(det["x_max"]))), int(round(float(det["y_max"])))
        color = COLORS.get(name, DEFAULT_COLOR)
        cv2.rectangle(canvas, (x1, y1), (x2, y2), color, 2)
        label = f"{name} {conf * 100:.1f}%"
        (tw, th), baseline = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.5, 1)
        y_text = max(y1, th + 6)
        cv2.rectangle(canvas, (x1, y_text - th - 6), (x1 + tw + 6, y_text + baseline - 2), color, -1)
        cv2.putText(canvas, label, (x1 + 3, y_text - 3), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1, cv2.LINE_AA)
    return canvas


def save_annotated_frame(source_path: Path, output_path: Path, detections: Iterable[Mapping]) -> str:
    image = cv2.imread(str(source_path))
    if image is None:
        raise ValueError(f"Unable to read frame for annotation: {source_path}")
    annotated = draw_detections(image, detections)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    if not cv2.imwrite(str(output_path), annotated, [cv2.IMWRITE_JPEG_QUALITY, 95]):
        raise ValueError(f"Unable to write annotated frame: {output_path}")
    return str(output_path)
