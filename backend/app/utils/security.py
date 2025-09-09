import os
import secrets

from cryptography.fernet import Fernet

from ..config import settings

if not settings.ENCRYPTION_KEY:
    pass


def fernet() -> Fernet:

    if not settings.ENCRYPTION_KEY:
        raise RuntimeError("ENCRYPTION_KEY is not set")
    return Fernet(settings.ENCRYPTION_KEY.encode() if isinstance(settings.ENCRYPTION_KEY, str) else settings.ENCRYPTION_KEY)


def encrypt(text: str) -> str:

    return fernet().encrypt(text.encode()).decode()


def decrypt(token: str) -> str:

    return fernet().decrypt(token.encode()).decode()


def new_state() -> str:

    return secrets.token_urlsafe(24)
