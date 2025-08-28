from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Iterable, Optional

import httpx
from sqlalchemy.orm import Session

from .. import models
from ..config import settings
from .security import decrypt, encrypt

GMAIL_API = "https://gmail.googleapis.com/gmail/v1/users"
TOKEN_URL = "https://oauth2.googleapis.com/token"


class GmailClient:
    """Minimal Gmail client that auto-refreshes access tokens and wraps key endpoints."""

    def __init__(self, db: Session, acct: models.GmailAccount):
        self.db = db
        self.acct = acct

    async def _ensure_token(self):
        now = datetime.now(timezone.utc)
        # Refresh 5 minutes early
        if self.acct.expiry and self.acct.expiry - now > timedelta(minutes=5):
            return
        if not self.acct.refresh_token:
            return  # cannot refresh
        refresh = decrypt(self.acct.refresh_token)
        async with httpx.AsyncClient(timeout=20) as client:
            data = {
                "client_id": settings.GOOGLE_CLIENT_ID,
                "client_secret": settings.GOOGLE_CLIENT_SECRET,
                "refresh_token": refresh,
                "grant_type": "refresh_token",
            }
            r = await client.post(TOKEN_URL, data=data)
            r.raise_for_status()
            payload = r.json()
            access_token = payload["access_token"]
            expires_in = payload.get("expires_in", 3600)
            new_expiry = now + timedelta(seconds=expires_in)
            # persist new token/expiry
            self.acct.access_token = encrypt(access_token)
            self.acct.expiry = new_expiry
            self.db.add(self.acct)
            self.db.commit()

    async def _auth_headers(self) -> Dict[str, str]:
        """helper method to build Authorization header"""
        await self._ensure_token()
        access = decrypt(
            self.acct.access_token) if self.acct.access_token else None
        return {"Authorization": f"Bearer {access}"}

    async def list_message_ids(self, q: Optional[str] = None, label_ids: Optional[Iterable[str]] = None):
        """Yield Gmail message IDs (IDs only) with optional query/labels."""
        url = f"{GMAIL_API}/me/messages"
        headers = await self._auth_headers()
        params: Dict[str, Any] = {"maxResults": 500}
        if q:
            params["q"] = q
        if label_ids:
            params["labelIds"] = list(label_ids)
        next_token = None
        async with httpx.AsyncClient(timeout=None) as client:
            while True:
                if next_token:
                    params["pageToken"] = next_token
                r = await client.get(url, headers=headers, params=params)
                r.raise_for_status()
                data = r.json()
                for m in data.get("messages", []):
                    yield m["id"]
                next_token = data.get("nextPageToken")
                if not next_token:
                    break

    async def get_message_full(self, message_id: str) -> Dict[str, Any]:
        url = f"{GMAIL_API}/me/messages/{message_id}"
        headers = await self._auth_headers()
        params = {"format": "FULL"}
        async with httpx.AsyncClient(timeout=30) as client:
            r = await client.get(url, headers=headers, params=params)
            r.raise_for_status()
            return r.json()

    async def get_history(self, start_history_id: str, page_token: Optional[str] = None) -> Dict[str, Any]:
        url = f"{GMAIL_API}/me/history"
        headers = await self._auth_headers()
        params: Dict[str, Any] = {
            "startHistoryId": start_history_id,
            "historyTypes": ["messageAdded", "messageDeleted", "labelsAdded", "labelsRemoved"],
            "maxResults": 1000,
        }
        if page_token:
            params["pageToken"] = page_token
        async with httpx.AsyncClient(timeout=30) as client:
            r = await client.get(url, headers=headers, params=params)
            r.raise_for_status()
            return r.json()

    async def get_profile(self) -> Dict[str, Any]:
        url = f"{GMAIL_API}/me/profile"
        headers = await self._auth_headers()
        async with httpx.AsyncClient(timeout=20) as client:
            r = await client.get(url, headers=headers)
            r.raise_for_status()
            return r.json()
