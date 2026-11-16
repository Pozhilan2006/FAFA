"""Team classification contract."""
from typing import Protocol
import numpy as np


class TeamClassifier(Protocol):
    def classify(self, crop: np.ndarray) -> tuple[str | None, float]: ...
