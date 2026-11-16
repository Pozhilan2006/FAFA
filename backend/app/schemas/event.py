"""Pydantic representation of event candidates."""
from typing import Literal
from pydantic import BaseModel, Field
from .observation import Point


class EventCandidate(BaseModel):
    event_id: str
    match_id: str
    event_type: str
    timestamp: float = Field(ge=0)
    source_track_id: str | None = None
    target_track_id: str | None = None
    source_global_player_id: str | None = None
    target_global_player_id: str | None = None
    confidence: float = Field(ge=0, le=1)
    status: Literal["candidate", "confirmed", "rejected"] = "candidate"
    location: Point | None = None
