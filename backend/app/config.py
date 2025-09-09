from pathlib import Path

from pydantic_settings import BaseSettings

BASE_DIR = Path(__file__).resolve().parent.parent


class Settings(BaseSettings):

    DATABASE_URL: str
    REDIS_URL: str
    ALLOW_ORIGIN: str

    JWT_SECRET: str
    SESSION_COOKIE_NAME: str
    GOOGLE_CLIENT_ID: str | None = None
    GOOGLE_CLIENT_SECRET: str | None = None
    GOOGLE_REDIRECT_URI: str | None = None
    GOOGLE_OAUTH_SCOPES: str | None = None

    PINECONE_API_KEY: str | None = None
    PINECONE_INDEX: str | None = None
    EMBEDDING_MODEL: str | None = None
    EMBEDDING_DIM: int | None = None
    ENCRYPTION_KEY: str | None = None
    APP_BASE_URL: str
    OPENAI_API_KEY: str | None = None
    OPENAI_CHAT_MODEL: str | None = None

    class Config:
        env_file = str(BASE_DIR / ".env")
        extra = "ignore"


settings = Settings()  # loads from env
