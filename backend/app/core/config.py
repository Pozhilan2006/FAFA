"""Environment-backed application settings."""
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "Football Analytics Platform"
    environment: str = "development"
    database_url: str = "postgresql+psycopg://football:change_me@localhost:5432/football_analytics"
    cors_origins: str = "http://localhost:3000"
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


settings = Settings()
