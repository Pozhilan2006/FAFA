"""Validate incoming vision data before future persistence."""
from ..schemas.observation import Observation
from ..schemas.event import EventCandidate


def validate_ingestion(observations: list[Observation], events: list[EventCandidate]) -> dict[str, int]:
    return {"accepted_observations": len(observations), "accepted_event_candidates": len(events)}
