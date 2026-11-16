"""Object detector contract; no model is bundled."""
from dataclasses import dataclass
from typing import Protocol
import numpy as np


@dataclass(frozen=True)
class Detection:
    class_name: str
    confidence: float
    bounding_box: tuple[float, float, float, float]


class ObjectDetector(Protocol):
    """A future detector accepts BGR frames and returns candidate detections."""
    def detect(self, frame: np.ndarray) -> list[Detection]: ...


class UnavailableObjectDetector:
    """Explicit placeholder that never claims to detect objects."""
    def detect(self, frame: np.ndarray) -> list[Detection]:
        raise NotImplementedError("No detection model is configured; model inference is deferred.")
