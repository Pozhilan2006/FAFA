"""Lazy, reusable YOLO model loader with CPU/CUDA selection and cached instance."""
from __future__ import annotations

import logging
import threading
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from ...core.config import settings

logger = logging.getLogger(__name__)

_lock = threading.Lock()
_cached: dict[str, tuple[Any, "ModelInfo"]] = {}


@dataclass(frozen=True)
class ModelInfo:
    model_name: str
    model_path: str | None
    device: str
    class_names: dict[int, str]
    supported_target_classes: list[str]


def _resolve_device(requested: str | None) -> str:
    if requested:
        return requested
    try:
        import torch

        return "cuda" if torch.cuda.is_available() else "cpu"
    except Exception:
        return "cpu"


def _resolve_model_source() -> tuple[str, str | None]:
    path = (settings.detection_model_path or "").strip() or None
    name = (settings.detection_model_name or "").strip() or "yolov8n.pt"
    if path:
        p = Path(path)
        if not p.is_absolute():
            p = Path(path).resolve()
        if not p.is_file():
            raise FileNotFoundError(f"Configured detection model weights were not found: {p}")
        return str(p), str(p)
    candidate = Path(name)
    if candidate.suffix in {".pt", ".onnx", ".engine"} and candidate.exists():
        return str(candidate.resolve()), str(candidate.resolve())
    return name, None


def get_model_info(model: Any, model_name: str, model_path: str | None, device: str) -> ModelInfo:
    names = getattr(model, "names", None) or {}
    if isinstance(names, list):
        class_names = {i: str(n) for i, n in enumerate(names)}
    else:
        class_names = {int(k): str(v) for k, v in dict(names).items()}
    supported = [n for n in class_names.values() if n in {"person", "sports ball"}]
    return ModelInfo(
        model_name=model_name,
        model_path=model_path,
        device=device,
        class_names=class_names,
        supported_target_classes=supported,
    )


def load_model(force_reload: bool = False) -> tuple[Any, ModelInfo]:
    """Load and cache the configured YOLO model once; no loading occurs at app startup."""
    source, resolved_path = _resolve_model_source()
    device = _resolve_device(settings.detection_device)
    cache_key = f"{source}|{device}"
    with _lock:
        if not force_reload and cache_key in _cached:
            return _cached[cache_key]
        try:
            from ultralytics import YOLO
        except Exception as exc:  # pragma: no cover - dependency/environment specific
            raise RuntimeError(
                "Ultralytics YOLO is not installed. Install compatible 'ultralytics' and PyTorch packages to run detection."
            ) from exc
        logger.info("Loading detection model '%s' on device '%s'", source, device)
        try:
            model = YOLO(source)
        except Exception as exc:
            raise RuntimeError(f"Failed to initialize YOLO model from '{source}': {exc}") from exc
        try:
            model.to(device)
        except Exception as exc:
            logger.warning("Could not move model to '%s', falling back to default device: %s", device, exc)
            device = str(getattr(model, "device", device))
        info = get_model_info(model, Path(source).name if resolved_path else source, resolved_path, device)
        logger.info("Detection model ready: %s (%s), classes=%s", info.model_name, info.device, len(info.class_names))
        _cached[cache_key] = (model, info)
        return _cached[cache_key]


def describe_model() -> dict[str, Any]:
    source, resolved_path = _resolve_model_source()
    device = _resolve_device(settings.detection_device)
    cache_key = f"{source}|{device}"
    with _lock:
        cached = _cached.get(cache_key)
    if cached:
        _, info = cached
        return {
            "model_name": info.model_name,
            "model_path": info.model_path,
            "device": info.device,
            "loaded": True,
            "class_names": info.class_names,
            "supported_target_classes": info.supported_target_classes,
        }
    return {
        "model_name": Path(source).name if resolved_path else source,
        "model_path": resolved_path,
        "device": device,
        "loaded": False,
        "class_names": None,
        "supported_target_classes": ["person", "sports ball"],
    }
