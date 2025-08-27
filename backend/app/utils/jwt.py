from datetime import datetime, timedelta, timezone

from fastapi import HTTPException, Request, Response, status
from jose import JWTError, jwt

from ..config import settings

ALGO = "HS256"
COOKIE_NAME = settings.SESSION_COOKIE_NAME


def issue_session_cookie(resp: Response, user_id: str):
    exp = datetime.now(timezone.utc) + timedelta(days=7)
    token = jwt.encode({"sub": user_id, "exp": exp},
                       settings.JWT_SECRET, algorithm=ALGO)
    resp.set_cookie(
        key=COOKIE_NAME,
        value=token,
        httponly=True,
        secure=False,  # set True in prod (HTTPS)
        samesite="lax",
        max_age=7*24*3600,
        path="/",
    )


def clear_session_cookie(resp: Response):
    resp.delete_cookie(COOKIE_NAME, path="/")


def get_user_id_from_cookie(req: Request) -> str | None:
    token = req.cookies.get(COOKIE_NAME)
    if not token:
        return None
    try:
        payload = jwt.decode(token, settings.JWT_SECRET, algorithms=[ALGO])
        return payload.get("sub")
    except JWTError:
        return None
