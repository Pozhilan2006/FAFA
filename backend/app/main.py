"""Application entry point."""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .api import clubs, matches, players, teams, videos, vision
from .api.routes import detection
from .core.config import settings
from .database.base import Base
from .database.connection import engine
from .database import models  # noqa: F401

app = FastAPI(title=settings.app_name, version="0.1.0")
app.add_middleware(CORSMiddleware, allow_origins=["http://localhost:3000", "http://localhost:3001"], allow_methods=["*"], allow_headers=["*"], allow_credentials=True)
for router in (clubs.router, teams.router, players.router, matches.router, videos.router, vision.router, detection.router):
    app.include_router(router, prefix="/api")

@app.on_event("startup")
def initialise_storage_and_database() -> None:
    settings.storage_path.mkdir(parents=True, exist_ok=True)
    (settings.storage_path / "detections" / "annotated_frames").mkdir(parents=True, exist_ok=True)
    (settings.storage_path / "detections" / "results").mkdir(parents=True, exist_ok=True)
    Base.metadata.create_all(engine)

@app.get("/health")
@app.get("/api/health")
def health() -> dict[str, str]:
    return {"status": "ok", "environment": settings.environment}
