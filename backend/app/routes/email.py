# app/routes/emails.py
from app import models
from app.db import get_db
from app.utils.jwt import get_user_id_from_cookie
from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from ..schemas import EmailDetail

router = APIRouter(prefix="/emails", tags=["emails"])


def _ensure_uid(request: Request) -> str:
    uid = get_user_id_from_cookie(request)
    if not uid:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")
    return uid


def _gmail_web_url(message_id: str | None, thread_id: str | None) -> str | None:
    if message_id:
        return f"https://mail.google.com/mail/u/0/#inbox/{message_id}"
    if thread_id:
        return f"https://mail.google.com/mail/u/0/#all/{thread_id}"
    return None


def _to_detail(row: models.EmailMessage) -> EmailDetail:
    return EmailDetail(
        id=str(row.id),
        gmail_account_id=str(row.gmail_account_id),
        message_id=row.message_id,
        thread_id=row.thread_id,
        subject=row.subject,
        from_addr=row.from_addr,
        to_addr=row.to_addr,
        cc=row.cc,
        bcc=row.bcc,
        date=row.date.isoformat() if row.date else None,
        snippet=row.snippet,
        body_text=row.body_text,
        body_html=row.body_html,
        headers_json=row.headers_json,
        label_ids=row.label_ids,
        gmail_web_url=_gmail_web_url(row.message_id, row.thread_id),
    )


@router.get("/{email_id}", response_model=EmailDetail, response_model_exclude_none=True)
async def get_email_by_db_id(email_id: str, request: Request, db: Session = Depends(get_db)):
    uid = _ensure_uid(request)
    acct_ids = [a.id for a in db.query(models.GmailAccount).filter(
        models.GmailAccount.user_id == uid).all()]
    if not acct_ids:
        raise HTTPException(400, "No linked Gmail account")

    row = (db.query(models.EmailMessage)
             .filter(models.EmailMessage.id == email_id,
                     models.EmailMessage.gmail_account_id.in_(acct_ids))
             .one_or_none())
    if not row:
        raise HTTPException(404, "Email not found")
    return _to_detail(row)


@router.get("/by-gmail/{message_id}", response_model=EmailDetail, response_model_exclude_none=True)
async def get_email_by_message_id(message_id: str, request: Request, db: Session = Depends(get_db)):
    uid = _ensure_uid(request)
    acct_ids = [a.id for a in db.query(models.GmailAccount).filter(
        models.GmailAccount.user_id == uid).all()]
    if not acct_ids:
        raise HTTPException(400, "No linked Gmail account")

    row = (db.query(models.EmailMessage)
             .filter(models.EmailMessage.message_id == message_id,
                     models.EmailMessage.gmail_account_id.in_(acct_ids))
             .one_or_none())
    if not row:
        raise HTTPException(404, "Email not found")
    return _to_detail(row)
