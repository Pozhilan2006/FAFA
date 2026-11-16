"""Application entry point."""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .api import clubs, matches, players, teams, videos, vision
from .core.config import settings

app = FastAPI(title=settings.app_name, version="0.1.0")
app.add_middleware(CORSMiddleware, allow_origins=[origin.strip() for origin in settings.cors_origins.split(",")], allow_methods=["*"], allow_headers=["*"], allow_credentials=True)
for router in (clubs.router, teams.router, players.router, matches.router, videos.router, vision.router):
    app.include_router(router, prefix="/api")

@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "environment": settings.environment}
