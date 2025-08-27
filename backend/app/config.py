from pathlib import Path

from pydantic_settings import BaseSettings

BASE_DIR = Path(__file__).resolve().parent.parent


class Settings(BaseSettings):

    DATABASE_URL: str
    REDIS_URL: str = "redis://localhost:6379/0"
    ALLOW_ORIGIN: str = "http://localhost:3000"

    JWT_SECRET: str = "dev-secret"
    SESSION_COOKIE_NAME: str = "maillens_session"
    GOOGLE_CLIENT_ID: str | None = None
    GOOGLE_CLIENT_SECRET: str | None = None
    GOOGLE_REDIRECT_URI: str | None = None
    GOOGLE_OAUTH_SCOPES: str | None = None

    PINECONE_API_KEY: str | None = None
    PINECONE_INDEX: str | None = None
    EMBEDDING_MODEL: str | None = None
    EMBEDDING_DIM: int | None = None
    ENCRYPTION_KEY: str | None = None
    APP_BASE_URL: str = "http://localhost:3000"

    class Config:
        env_file = str(BASE_DIR / ".env")
        extra = "ignore"


settings = Settings()  # loads from env
