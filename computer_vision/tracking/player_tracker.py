"""Player-tracker interface."""
from typing import Protocol
from computer_vision.detection.object_detector import Detection


class PlayerTracker(Protocol):
    """Assign video-local track IDs; permanent identity is intentionally separate."""
    def update(self, detections: list[Detection], frame_number: int) -> dict[str, Detection]: ...
