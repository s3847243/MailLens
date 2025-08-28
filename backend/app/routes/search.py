from __future__ import annotations

from typing import Any, List

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy.orm import Session

from .. import models
from ..db import get_db
from ..utils.embeddings import embed_text
from ..utils.jwt import get_user_id_from_cookie
from ..utils.vectorstore import query_top_k

router = APIRouter(prefix="/search", tags=["search"])


@router.get("")
async def search_emails(q: str = Query(..., min_length=1), topK: int = Query(8, ge=1, le=50), request: Request = None, db: Session = Depends(get_db)):
    uid = get_user_id_from_cookie(request)
    if not uid:
        raise HTTPException(status_code=401, detail="Not authenticated")

    acct = db.query(models.GmailAccount).filter(
        models.GmailAccount.user_id == uid).first()
    if not acct:
        raise HTTPException(status_code=400, detail="No linked Gmail account")

    vec = await embed_text(q)
    if vec is None:
        return {"results": []}
    matches = await query_top_k(namespace=str(acct.id), vector=vec, top_k=topK)

    # hydrate from DB and build pills
    results: List[dict[str, Any]] = []
    ids = [m.id for m in matches]
    if not ids:
        return {"results": []}
    # Fetch all in one query
    rows = (
        db.query(models.EmailMessage)
        .filter(models.EmailMessage.message_id.in_(ids), models.EmailMessage.gmail_account_id == acct.id)
        .all()
    )
    row_by_mid = {r.message_id: r for r in rows}
    for m in matches:
        r = row_by_mid.get(m.id)
        if not r:
            continue
        results.append({
            "id": str(r.id),
            "messageId": r.message_id,
            "threadId": r.thread_id,
            "subject": r.subject,
            "from": r.from_addr,
            "date": (r.date.isoformat() if r.date else None),
            "snippet": r.snippet,
            "score": float(m.score) if hasattr(m, "score") else None,
            "source": "Gmail",
        })
    return {"query": q, "results": results}
