from typing import List
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", case_sensitive=True)

    DATABASE_URL: str
    SECRET_KEY: str
    BACKEND_CORS_ORIGINS: List[str] = ["http://localhost:3000"]
    ENVIRONMENT: str = "development"

    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24  # 24 hours

    # RSS Producer Job Settings
    RSS_FETCH_INTERVAL_MINUTES: int = 1
    RSS_FETCH_CONCURRENCY: int = 50
    BACKEND_TG_SESSION_STRING: str
    BACKEND_TG_API_ID: int
    BACKEND_TG_API_HASH: str
    BACKEND_AWS_ACCESS_KEY: str
    BACKEND_AWS_SECRET_KEY: str
    BACKEND_AWS_REGION: str


settings = Settings()
