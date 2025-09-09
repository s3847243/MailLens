from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, List, Tuple

from sqlalchemy.orm import Session

from .. import models
from ..utils.embeddings import embed_text
from ..utils.vectorstore import query_top_k

MAX_CONTEXT_CHARS = 8000
MAX_HISTORY_CHARS = 6000
MAX_TURNS = 6  # include last N prior messages (user/assistant)
SYSTEM_PROMPT = (
    "You are MailLens, an email research assistant. Use the provided email excerpts when relevant. "
    "Cite sources with bracketed numbers like [1], [2]. Be concise and do not fabricate details. If you find the question irrelevant to the excerpts then reply by saying - Please ask questions relevant to the emails."
)


def collapse_chunk_matches_to_messages(matches: List[Any], top_k_messages: int = 8, min_score: float = 0.2
                                       ) -> List[Tuple[str, float, Any]]:
    """
    Normalize Pinecone matches (which are chunk-level) into distinct message_ids.
    Returns a list of (message_id, best_score, best_match_obj), sorted by score desc.
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

    rows: List[Tuple[str, float, Any]] = sorted(
        [(mid, sc, mm) for mid, (sc, mm) in best.items()],
        key=lambda t: t[1],
        reverse=True
    )
    return rows[:top_k_messages]


def build_context_and_pills_from_message_ids(
    db: Session,
    acct_id,
    message_rows: List[Tuple[str, float, Any]],
    body_chars: int = 800
) -> tuple[str, list[dict]]:
    """
    Given (message_id, score, match) tuples, hydrate rows and build:
      - context: a stitched string the LLM can read
      - pills:   metadata for UI
    """
    mids = [mid for (mid, _, _) in message_rows]
    if not mids:
        return "", []

    rows = (
        db.query(models.EmailMessage)
        .filter(
            models.EmailMessage.gmail_account_id == acct_id,
            models.EmailMessage.message_id.in_(mids),
        )
        .all()
    )
    by_mid = {r.message_id: r for r in rows}

    context_parts: List[str] = []
    pills: List[dict] = []

    rank = 0
    for mid, score, match in message_rows:
        r = by_mid.get(mid)
        if not r:
            continue
        rank += 1
        body_preview = (r.body_text or r.snippet or "")[:body_chars].strip()

        context_parts.append(
            f"=== Email #{rank} ===\n"
            f"Subject: {r.subject or '(no subject)'}\n"
            f"From: {r.from_addr or ''}\n"
            f"To: {r.to_addr or ''}\n"
            f"Date: {r.date.isoformat() if r.date else ''}\n"
            f"Snippet: {r.snippet or ''}\n"
            f"Excerpt:\n{body_preview}\n"
        )

        pills.append({
            "id": str(r.id),
            "messageId": r.message_id,
            "threadId": r.thread_id,
            "subject": r.subject,
            "from": r.from_addr,
            "date": (r.date.isoformat() if r.date else None),
            "snippet": r.snippet,
            "score": score,
            "source": "Gmail",
        })

    context = "\n".join(context_parts)
    return context, pills


def _load_chat_history(db: Session, chat_id: str) -> List[Dict[str, str]]:
    """Return recent chat turns as OpenAI messages (without citations)."""
    msgs = (
        db.query(models.ChatMessage)
        .filter(models.ChatMessage.chat_session_id == chat_id)
        .order_by(models.ChatMessage.created_at.asc())
        .all()
    )
    msgs = msgs[-MAX_TURNS*2:]

    def clean(content: str | None) -> str:

        c = (content or "").strip()
        return c[:2000]

    out: List[Dict[str, str]] = []
    for m in msgs:
        if m.role not in {"user", "assistant", "system"}:
            continue
        if m.role == "assistant" and m.citations:
            pass
    out.append({"role": m.role, "content": clean(m.content)})

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
