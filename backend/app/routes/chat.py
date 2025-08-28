from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import AsyncGenerator, List, Optional

from fastapi import (APIRouter, Depends, HTTPException, Query, Request,
                     Response, status)
from fastapi.responses import StreamingResponse
from sqlalchemy import and_, or_
from sqlalchemy.orm import Session

from .. import models
from ..db import get_db
from ..services.rag import (_build_context_and_pills, _load_chat_history,
                            build_messages)
from ..utils.embeddings import embed_text
from ..utils.jwt import get_user_id_from_cookie
from ..utils.llm import stream_chat
from ..utils.vectorstore import query_top_k

router = APIRouter(prefix="/chats", tags=["chat"])
# --- helpers ---


def _require_user(request: Request) -> str:

    uid = get_user_id_from_cookie(request)
    if not uid:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                            detail="Not authenticated")
    return uid

# --- CRUD ---


@router.post("")
async def create_chat(request: Request, db: Session = Depends(get_db)):
    uid = _require_user(request)
    cs = models.ChatSession(user_id=uid, title=None, created_at=datetime.now(
        timezone.utc), updated_at=datetime.now(timezone.utc))
    db.add(cs)
    db.commit()
    return {"id": str(cs.id)}


@router.get("")
async def list_chats(request: Request, db: Session = Depends(get_db)):
    uid = _require_user(request)
    rows = (
        db.query(models.ChatSession)
        .filter(models.ChatSession.user_id == uid)
        .order_by(models.ChatSession.updated_at.desc())
        .all()
    )
    return [{"id": str(r.id), "title": r.title, "updated_at": r.updated_at.isoformat()} for r in rows]


@router.delete("/{chat_id}")
async def delete_chat(chat_id: str, request: Request, db: Session = Depends(get_db)):
    uid = _require_user(request)
    row = (
        db.query(models.ChatSession)
        .filter(models.ChatSession.id == chat_id, models.ChatSession.user_id == uid)
        .one_or_none()
    )
    if not row:
        raise HTTPException(status_code=404, detail="Chat not found")
    # cascade via ORM relationship is not configured here; delete messages manually or rely on FK cascade if set
    db.delete(row)
    db.commit()
    return {"ok": True}
# --- SSE ask ---


@router.post("/{chat_id}/ask")
async def chat_ask(chat_id: str, request: Request, db: Session = Depends(get_db)):
    uid = _require_user(request)
    chat = (
        db.query(models.ChatSession)
        .filter(models.ChatSession.id == chat_id, models.ChatSession.user_id == uid)
        .one_or_none()
    )
    if not chat:
        raise HTTPException(status_code=404, detail="Chat not found")

    payload = await request.json()
    question = (payload.get("q") or "").strip()
    if not question:
        raise HTTPException(status_code=400, detail="Empty question")

    # persist user message
    user_msg = models.ChatMessage(
        chat_session_id=chat.id,
        role="user",
        content=question,
        created_at=datetime.now(timezone.utc),
    )
    db.add(user_msg)
    db.commit()
    # find the gmail account for this user
    acct = db.query(models.GmailAccount).filter(
        models.GmailAccount.user_id == uid).first()
    if not acct:
        raise HTTPException(status_code=400, detail="No linked Gmail account")

    async def event_stream() -> AsyncGenerator[bytes, None]:
        # 1) notify searching state
        yield b"event: state\n"
        yield b"data: {\"value\": \"searching\"}\n\n"
        # 2) retrieval
        qvec = await embed_text(question)
        matches = []
        if qvec is not None:
            matches = await query_top_k(namespace=str(acct.id), vector=qvec, top_k=8)
        context, pills = _build_context_and_pills(
            db, acct_id=acct.id, matches=matches)
        # load prior chat history (after we've just saved the user message)
        history = _load_chat_history(db, str(chat.id))
        yield b"event: state\n"
        yield b"data: {\"value\": \"answering\"}\n\n"
        # 3) stream LLM tokens
        messages = build_messages(question, context)
        assistant_text_parts: list[str] = []
        async for delta in stream_chat(messages):
            assistant_text_parts.append(delta)
            packet = json.dumps({"delta": delta})
            yield b"event: message\n" + (b"data: " + packet.encode("utf-8") + b"\n\n")

        final_text = "".join(assistant_text_parts)
        # 4) persist assistant message with citations
        asst_msg = models.ChatMessage(
            chat_session_id=chat.id,
            role="assistant",
            content=final_text,
            citations=pills,  # store the pills as JSONB
            created_at=datetime.now(timezone.utc),
        )
        db.add(asst_msg)
        # update chat title on first question
        if not chat.title:
            chat.title = question[:60]
        chat.updated_at = datetime.now(timezone.utc)
        db.add(chat)
        db.commit()
        # 5) send final event with citations
        final_packet = json.dumps({"citations": pills})
        yield b"event: final\n" + (b"data: " + final_packet.encode("utf-8") + b"\n\n")

    return StreamingResponse(event_stream(), media_type="text/event-stream")


@router.get("/{chat_id}/messages")
async def list_chat_messages(
    chat_id: str,
    request: Request,
    db: Session = Depends(get_db),
    limit: int = Query(100, ge=1, le=200),
    after: Optional[str] = Query(
        None, description="Return messages strictly after this message_id (cursor)"),
):
    """
    Return messages for a chat session, oldest-first.
    - `limit` caps the number of returned rows (default 100).
    - `after` (optional) is a cursor = message_id; returns messages after that one.
    """
    uid = _require_user(request)

    chat = (
        db.query(models.ChatSession)
        .filter(models.ChatSession.id == chat_id, models.ChatSession.user_id == uid)
        .one_or_none()
    )
    if not chat:
        raise HTTPException(status_code=404, detail="Chat not found")

    # Build base query
    q = (
        db.query(models.ChatMessage)
        .filter(models.ChatMessage.chat_session_id == chat_id)
    )

    # Cursor pagination (after = message_id)
    if after:
        anchor = (
            db.query(models.ChatMessage)
            .filter(models.ChatMessage.id == after, models.ChatMessage.chat_session_id == chat_id)
            .one_or_none()
        )
        if not anchor:
            raise HTTPException(
                status_code=400, detail="Invalid 'after' cursor")
        # Return messages strictly after the anchor (by created_at, then id)
        q = q.filter(
            or_(
                models.ChatMessage.created_at > anchor.created_at,
                and_(
                    models.ChatMessage.created_at == anchor.created_at,
                    models.ChatMessage.id > anchor.id,
                ),
            )
        )

    # Oldest-first for easy rendering
    q = q.order_by(models.ChatMessage.created_at.asc(),
                   models.ChatMessage.id.asc()).limit(limit)

    rows: List[models.ChatMessage] = q.all()

    # Prepare a next cursor if there might be more
    next_cursor = rows[-1].id if rows and len(rows) == limit else None

    def serialize(m: models.ChatMessage):
        return {
            "id": str(m.id),
            "role": m.role,                    # "user" | "assistant"
            "content": m.content,
            # JSONB pills for assistant turns (may be [])
            "citations": m.citations or [],
            "created_at": m.created_at.isoformat(),
        }

    return {
        "chat_id": str(chat.id),
        "messages": [serialize(m) for m in rows],
        "next_cursor": str(next_cursor) if next_cursor else None,
    }
