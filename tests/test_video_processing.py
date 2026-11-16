import pytest
from computer_vision.video_processing.video_loader import validate_video_path


def test_invalid_video_path_is_explicit() -> None:
    with pytest.raises(FileNotFoundError):
        validate_video_path("missing.mp4")
