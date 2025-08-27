from datetime import datetime, timedelta, timezone
from urllib.parse import urlencode

import httpx

from ..config import settings

AUTH_URL = "https://accounts.google.com/o/oauth2/v2/auth"
TOKEN_URL = "https://oauth2.googleapis.com/token"
USERINFO_URL = "https://openidconnect.googleapis.com/v1/userinfo"

SCOPES = (settings.GOOGLE_OAUTH_SCOPES or "").split()


def build_auth_url(state: str) -> str:
    params = {
        "client_id": settings.GOOGLE_CLIENT_ID,
        "redirect_uri": settings.GOOGLE_REDIRECT_URI,
        "response_type": "code",
        "scope": " ".join(SCOPES),
        "access_type": "offline",
        "prompt": "consent",
        "include_granted_scopes": "true",
        "state": state,
    }
    return f"{AUTH_URL}?{urlencode(params)}"


async def exchange_code_for_tokens(code: str):
    async with httpx.AsyncClient(timeout=20) as client:
        data = {
            "code": code,
            "client_id": settings.GOOGLE_CLIENT_ID,
            "client_secret": settings.GOOGLE_CLIENT_SECRET,
            "redirect_uri": settings.GOOGLE_REDIRECT_URI,
            "grant_type": "authorization_code",
        }
        r = await client.post(TOKEN_URL, data=data)
        r.raise_for_status()
        payload = r.json()
        # normalize
        access_token = payload["access_token"]
        refresh_token = payload.get("refresh_token")
        expires_in = payload.get("expires_in", 3600)
        expiry = datetime.now(timezone.utc) + timedelta(seconds=expires_in)
        return access_token, refresh_token, expiry, payload


async def fetch_userinfo(access_token: str):
    async with httpx.AsyncClient(timeout=20) as client:
        r = await client.get(USERINFO_URL, headers={"Authorization": f"Bearer {access_token}"})
        r.raise_for_status()
        return r.json()
