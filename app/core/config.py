from functools import lru_cache

from pydantic import model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Application settings, loaded from environment variables.
    """

    APP_NAME: str = "A-EYE AI Analysis Service"
    APP_VERSION: str = "1.0.0"
    APP_DESCRIPTION: str = "A FastAPI service for wellness image analysis, as detailed in the SRS."

    POSTGRES_USER: str = "postgres"
    POSTGRES_PASSWORD: str = "password"
    POSTGRES_SERVER: str = "localhost"
    POSTGRES_PORT: int = 5433
    POSTGRES_DB: str = "a_eye_db"

    DATABASE_URL: str | None = None

    @model_validator(mode="before")
    @classmethod
    def assemble_db_url(cls, data: dict) -> dict:
        if not data.get("DATABASE_URL"):
            user = data.get("POSTGRES_USER", "postgres")
            password = data.get("POSTGRES_PASSWORD", "password")
            server = data.get("POSTGRES_SERVER", "localhost")
            port = data.get("POSTGRES_PORT", 5433)
            db = data.get("POSTGRES_DB", "a_eye_db")
            data["DATABASE_URL"] = f"postgresql+psycopg2://{user}:{password}@{server}:{port}/{db}"
        
        redis_url = data.get("REDIS_URL", "redis://localhost:6380/0")
        if not data.get("CELERY_BROKER_URL"):
            data["CELERY_BROKER_URL"] = redis_url
        if not data.get("CELERY_RESULT_BACKEND"):
            data["CELERY_RESULT_BACKEND"] = redis_url
            
        return data

    REDIS_URL: str = "redis://localhost:6380/0"

    CELERY_BROKER_URL: str = "redis://localhost:6380/0"
    CELERY_RESULT_BACKEND: str = "redis://localhost:6380/0"

    STORAGE_TYPE: str = "local"
    LOCAL_STORAGE_PATH: str = "uploads"

    S3_BUCKET_NAME: str | None = None
    S3_ACCESS_KEY_ID: str | None = None
    S3_SECRET_ACCESS_KEY: str | None = None
    S3_ENDPOINT_URL: str | None = None

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
