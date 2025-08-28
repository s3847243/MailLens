from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session

from .. import models
from ..db import get_db
from ..utils.gmail_client import GmailClient
from ..utils.jwt import get_user_id_from_cookie

router = APIRouter(prefix="/gmail", tags=["gmail"])


def _get_acct(request: Request, db: Session) -> models.GmailAccount:
    uid = get_user_id_from_cookie(request)
    if not uid:
        raise HTTPException(status_code=401, detail="Not authenticated")
    acct = (
        db.query(models.GmailAccount)
        .join(models.User)
        .filter(models.User.id == uid)
        .first()
    )
    if not acct:
        raise HTTPException(status_code=400, detail="No linked Gmail account")
    return acct


@router.get("/list")
async def list_ids(request: Request, db: Session = Depends(get_db)):
    acct = _get_acct(request, db)
    client = GmailClient(db, acct)
    ids = []
    async for mid in client.list_message_ids():
        ids.append(mid)
    return {"count": len(ids), "ids": ids[:50]}  # preview first 50


@router.get("/message/{message_id}")
async def get_message(message_id: str, request: Request, db: Session = Depends(get_db)):
    acct = _get_acct(request, db)
    client = GmailClient(db, acct)
    full = await client.get_message_full(message_id)
    return full
