from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, List, Tuple

from sqlalchemy.orm import Session

from .. import models
from ..utils.embeddings import embed_text
from ..utils.vectorstore import query_top_k

# Basic byte budget for context to avoid over-long prompts
MAX_CONTEXT_CHARS = 8000
MAX_HISTORY_CHARS = 6000
MAX_TURNS = 6  # include last N prior messages (user/assistant)
SYSTEM_PROMPT = (
    "You are MailLens, an email research assistant. Use the provided email excerpts when relevant. "
    "Cite sources with bracketed numbers like [1], [2]. Be concise and do not fabricate details."
)


def _build_context_and_pills(db: Session, acct_id: str, matches) -> Tuple[str, List[Dict[str, Any]]]:
    """Hydrate top-K matches into a context string and a list of citation pills."""
    ids = [m.id for m in matches]
    if not ids:
        return "", []
    rows = (
        db.query(models.EmailMessage)
        .filter(models.EmailMessage.message_id.in_(ids), models.EmailMessage.gmail_account_id == acct_id)
        .all()
    )
    # preserve match order
    by_id = {r.message_id: r for r in rows}
    context_parts: List[str] = []
    pills: List[Dict[str, Any]] = []
    total = 0
    for idx, m in enumerate(matches, start=1):
        r = by_id.get(m.id)
        if not r:
            continue
        # pill first; will be returned at the end
        pills.append({
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
        # context excerpt (trim body)
        body = r.body_text or ""
        excerpt = body[:1500]
        block = f"[{idx}] Subject: {r.subject or ''}\nFrom: {r.from_addr or ''}\nDate: {r.date.isoformat() if r.date else ''}\n---\n{excerpt}\n\n"
        if total + len(block) <= MAX_CONTEXT_CHARS:
            context_parts.append(block)
            total += len(block)
        else:
            break
    return "".join(context_parts), pills


def _load_chat_history(db: Session, chat_id: str) -> List[Dict[str, str]]:
    """Return recent chat turns as OpenAI messages (without citations)."""
    msgs = (
        db.query(models.ChatMessage)
        .filter(models.ChatMessage.chat_session_id == chat_id)
        .order_by(models.ChatMessage.created_at.asc())
        .all()
    )
    # keep the last MAX_TURNS*2 messages (user+assistant pairs)
    msgs = msgs[-MAX_TURNS*2:]

    def clean(content: str | None) -> str:

        c = (content or "").strip()
        # avoid pushing prior citation JSON into prompt
        return c[:2000]

    out: List[Dict[str, str]] = []
    for m in msgs:
        if m.role not in {"user", "assistant", "system"}:
            continue
        if m.role == "assistant" and m.citations:
            # strip any citation rendering text if present in content (we keep it simple)
            pass
    out.append({"role": m.role, "content": clean(m.content)})

    # Trim to budget
    total = 0
    trimmed: List[Dict[str, str]] = []
    for m in reversed(out):  # start from latest
        if total + len(m["content"]) > MAX_HISTORY_CHARS:
            break
        trimmed.append(m)
        total += len(m["content"]) + 20
    trimmed.reverse()
    return trimmed


def build_messages(
    user_query: str,
    context: str,
    history: List[Dict[str, str]] | None = None
) -> List[Dict[str, str]]:
    messages: List[Dict[str, str]] = [
        {"role": "system", "content": SYSTEM_PROMPT}
    ]
    if history:
        messages.extend(history)

    user_block = (
        f"Query: {user_query}\n\n"
        f"Relevant email excerpts:\n{context if context else '(none)'}"
    )
    messages.append({"role": "user", "content": user_block})
    return messages
