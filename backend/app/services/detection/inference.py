"""Frame-based and batched YOLO inference over extracted frames."""
from __future__ import annotations

import time
from pathlib import Path
from typing import Any, Iterable

import cv2

from .postprocessing import parse_yolo_result


def load_frame_image(frame) -> tuple[Any, str]:
    path = Path(frame.processed_frame_path or frame.original_frame_path)
    image = cv2.imread(str(path))
    if image is None:
        raise ValueError(f"Unreadable frame image: {path}")
    return image, str(path)


def run_inference_on_frames(
    model: Any,
    frames: Iterable,
    confidence_threshold: float,
    batch_size: int = 8,
    device: str | None = None,
) -> dict[str, Any]:
    frames = list(frames)
    total = len(frames)
    started = time.perf_counter()
    per_frame: list[dict[str, Any]] = []
    processed = 0
    failed = 0
    total_detections = 0
    step = max(1, int(batch_size))
    for i in range(0, total, step):
        batch = frames[i : i + step]
        metas = []
        for frame in batch:
            try:
                image, image_path = load_frame_image(frame)
                metas.append((frame, image_path, image, None))
            except Exception as exc:
                failed += 1
                metas.append((frame, None, None, str(exc)))
        valid = [m for m in metas if m[3] is None]
        valid_images = [m[2] for m in valid]
        results = []
        if valid_images:
            try:
                predict_kwargs = {"conf": confidence_threshold, "verbose": False}
                if device:
                    predict_kwargs["device"] = device
                results = list(model.predict(valid_images, **predict_kwargs))
            except Exception as exc:
                for frame, image_path, _, _ in valid:
                    failed += 1
                    per_frame.append({"frame": frame, "error": f"Inference error: {exc}", "detections": [], "image_path": image_path})
                results = []
                valid = []
        for (frame, image_path, _, _), result in zip(valid, results):
            detections = parse_yolo_result(
                result,
                frame_number=int(frame.frame_number),
                timestamp_seconds=float(frame.timestamp_seconds),
                original_width=int(frame.original_width),
                original_height=int(frame.original_height),
                confidence_threshold=confidence_threshold,
            )
            processed += 1
            total_detections += len(detections)
            per_frame.append({"frame": frame, "error": None, "detections": detections, "image_path": image_path})
        for frame, image_path, _, error in metas:
            if error is not None:
                per_frame.append({"frame": frame, "error": error, "detections": [], "image_path": image_path})
    elapsed = max(time.perf_counter() - started, 1e-9)
    return {
        "results": per_frame,
        "processed_frames": processed,
        "failed_frames": failed,
        "total_detections": total_detections,
        "inference_seconds": elapsed,
        "frames_per_second": (processed / elapsed) if elapsed > 0 else 0.0,
        "avg_seconds_per_frame": (elapsed / processed) if processed else None,
    }
