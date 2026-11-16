from fastapi import APIRouter
router = APIRouter(prefix="/matches", tags=["matches"])
@router.get("")
def list_matches() -> dict[str, object]: return {"items": [], "detail": "Match management is not implemented."}
