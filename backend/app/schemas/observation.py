"""Pydantic representation of the shared observation contract."""
from pydantic import BaseModel, Field


class Point(BaseModel):
    x: float
    y: float


class BoundingBox(BaseModel):
    x1: float
    y1: float
    x2: float
    y2: float


class Observation(BaseModel):
    match_id: str
    track_id: str
    global_player_id: str | None = None
    team_id: str | None = None
    timestamp: float = Field(ge=0)
    frame_number: int = Field(ge=0)
    class_name: str
    confidence: float = Field(ge=0, le=1)
    bounding_box: BoundingBox
    image_position: Point
    pitch_position: Point | None = None
