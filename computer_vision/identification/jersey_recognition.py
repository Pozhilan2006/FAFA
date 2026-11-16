"""Jersey recognition contract."""
from typing import Protocol
import numpy as np


class JerseyRecognizer(Protocol):
    def recognize(self, crop: np.ndarray) -> tuple[str | None, float]: ...
