from fastapi import APIRouter
router = APIRouter(prefix="/clubs", tags=["clubs"])
@router.get("")
def list_clubs() -> dict[str, object]: return {"items": [], "detail": "Club management is not implemented."}
