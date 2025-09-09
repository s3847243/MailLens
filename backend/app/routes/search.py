from __future__ import annotations

from typing import Any, Dict, List, Optional, Tuple

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy.orm import Session

from .. import models
from ..db import get_db
from ..utils.embeddings import embed_text
from ..utils.jwt import get_user_id_from_cookie
from ..utils.vectorstore import query_top_k

router = APIRouter(prefix="/search", tags=["search"])


def _collapse_chunk_matches(
    matches: List[Any],
    min_score: float = 0.2,
    top_k_messages: int = 8,
) -> List[Tuple[str, float, Any]]:
    """
    Collapse chunk-level matches into unique message_ids, keeping the best-scoring
    chunk per message. Returns [(message_id, best_score, match_obj)] sorted desc.
    """
    best: Dict[str, Tuple[float, Any]] = {}
    for m in matches or []:
        md = getattr(m, "metadata", {}) or {}
        mid = md.get("message_id")
        if not mid:
            _id = getattr(m, "id", "") or ""
            mid = _id.split("#", 1)[0] if "#" in _id else _id
        if not mid:
            continue

        score = float(getattr(m, "score", 0.0) or 0.0)
        if score < min_score:
            continue

        prev = best.get(mid)
        if (not prev) or score > prev[0]:
            best[mid] = (score, m)

    rows = sorted(
        [(mid, sc, mm) for mid, (sc, mm) in best.items()],
        key=lambda x: x[1],
        reverse=True,
    )
    return rows[:top_k_messages]


@router.get("")
async def search_emails(
    q: str = Query(..., min_length=1),
    topK: int = Query(8, ge=1, le=50),
    request: Request = None,
    db: Session = Depends(get_db),
):
    uid = get_user_id_from_cookie(request)
    if not uid:
        raise HTTPException(status_code=401, detail="Not authenticated")

    acct = (
        db.query(models.GmailAccount)
        .filter(models.GmailAccount.user_id == uid)
        .first()
    )
    if not acct:
        raise HTTPException(status_code=400, detail="No linked Gmail account")

    vec = await embed_text(q)
    if vec is None:
        return {"query": q, "results": []}

    matches = await query_top_k(
        namespace=str(acct.id),
        vector=vec,
        top_k=min(topK * 3, 100),
        filter={"type": {"$eq": "email_chunk"}},
    )

    msg_rows = _collapse_chunk_matches(
        matches, min_score=0.2, top_k_messages=topK)
    mids = [mid for (mid, _, _) in msg_rows]
    if not mids:
        return {"query": q, "results": []}

    rows = (
        db.query(models.EmailMessage)
        .filter(
            models.EmailMessage.gmail_account_id == acct.id,
            models.EmailMessage.message_id.in_(mids),
        )
        .all()
    )
    by_mid = {r.message_id: r for r in rows}

    results: List[Dict[str, Any]] = []
    for mid, score, _m in msg_rows:
        r = by_mid.get(mid)
        if not r:
            continue
        results.append({
            "id": str(r.id),                               # DB UUID for modal
            "messageId": r.message_id,
            "threadId": r.thread_id,
            "subject": r.subject,
            "from": r.from_addr,
            "date": (r.date.isoformat() if r.date else None),
            "snippet": r.snippet,
            "score": float(score),
            "source": "Gmail",
        })

    return {"query": q, "results": results}
