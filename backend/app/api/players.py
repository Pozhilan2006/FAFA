from fastapi import APIRouter
router = APIRouter(prefix="/players", tags=["players"])
@router.get("")
def list_players() -> dict[str, object]: return {"items": [], "detail": "Player management is not implemented."}
