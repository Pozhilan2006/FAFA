"""Environment-backed application settings."""
from pydantic_settings import BaseSettings, SettingsConfigDict
from pathlib import Path


class Settings(BaseSettings):
    app_name: str = "Football Analytics Platform"
    environment: str = "development"
    database_url: str = "sqlite:///./storage/football_analytics.db"
    cors_origins: str = "http://localhost:3000"
    storage_path: Path = Path("storage")
    max_upload_size_mb: int = 2048
    max_frame_dimension: int = 1280
    detection_model_name: str = "yolov8n.pt"
    detection_model_path: str | None = None
    detection_device: str | None = None
    detection_default_confidence: float = 0.35
    detection_default_batch_size: int = 8
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


settings = Settings()
