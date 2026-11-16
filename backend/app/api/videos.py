from fastapi import APIRouter
router = APIRouter(prefix="/videos", tags=["videos"])
@router.get("")
def list_videos() -> dict[str, object]: return {"items": [], "detail": "Video processing is not implemented."}
