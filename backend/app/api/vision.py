from fastapi import APIRouter
from ..schemas.event import EventCandidate
from ..schemas.observation import Observation
from ..services.ingestion_service import validate_ingestion
router = APIRouter(prefix="/vision", tags=["vision"])
@router.post("/ingestions")
def ingest_vision(observations: list[Observation], events: list[EventCandidate]) -> dict[str, object]:
    """Accept validated records; persistence and analysis are not yet implemented."""
    return {**validate_ingestion(observations, events), "detail": "Validated only; no processing or persistence occurred."}
